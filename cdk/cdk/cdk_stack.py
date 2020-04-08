from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_s3_notifications,
)
from aws_cdk.aws_apigateway import EndpointType
from aws_cdk.aws_s3 import HttpMethods
from aws_cdk.core import Duration
from constant import Constant
import uuid
from aws_cdk.aws_iam import (
    Role,
    Policy,
    ManagedPolicy,
    ServicePrincipal,
    CfnInstanceProfile,
    Effect,
    PolicyStatement,
)

class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        #创建访问角色
        #  action -> statement -> policy -> role -> attach lambda
        actions = ["logs:CreateLogGroup",
                   "logs:CreateLogStream",
                   "logs:PutLogEvents",
                   "s3:GetObject",
                   "s3:PutObject"]

        policyStatement = PolicyStatement(actions=actions, effect=Effect.ALLOW)
        policyStatement.add_all_resources()

        policy_name = "{}-policy".format(Constant.PROJECT_NAME)
        lambda_policy = Policy(self, policy_name, policy_name=policy_name)

        lambda_policy.add_statements(policyStatement)

        role_name = "{}-role".format(Constant.PROJECT_NAME)
        access_role = Role(
            self, role_name,
            role_name=role_name,
            assumed_by=ServicePrincipal('lambda.amazonaws.com')
        )

        lambda_policy.attach_to_role(access_role)

        # 创建STS lambda
        sts_lambda = _lambda.Function(
            self, 'sts', function_name='sts',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='auth.handler',
            timeout=Duration.minutes(1),
            role=access_role,
        )
        sts_lambda.add_environment("ak", Constant.AK)
        sts_lambda.add_environment("sk", Constant.SK)

        base_api = apigw.RestApi(
            self, 'Endpoint',
            endpoint_types=[EndpointType.REGIONAL],
        )
        example_entity = base_api.root.add_resource('auth')
        example_entity_lambda_integration = apigw.LambdaIntegration(sts_lambda, proxy=False, integration_responses=[
            {
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            }
        ]
                                                                     )
        example_entity.add_method('GET', example_entity_lambda_integration,
                                  method_responses=[{
                                      'statusCode': '200',
                                      'responseParameters': {
                                          'method.response.header.Access-Control-Allow-Origin': True,
                                      }
                                  }
                                  ]
                                  )

        self.add_cors_options(example_entity)



        #创建缩略图lambda
        layer_cv2 = _lambda.LayerVersion(
            self, 'cv2',
            code=_lambda.Code.from_bucket(s3.Bucket.from_bucket_name(self, "cdk-data-layer", bucket_name='nowfox'),
                                          'cdk-data/cv2.zip'),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_7],
        )

        lambda_thum = _lambda.Function(
            self, 'thum',function_name='thum',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='thum.handler',
            timeout=Duration.minutes(1),
            role=access_role,
        )
        lambda_thum.add_environment("frame_second", "3")
        lambda_thum.add_layers(layer_cv2)

        # 创建存储上传图片的bucket
        s3_bucket_name = "{}-{}".format("upload", self._get_UUID(4))
        s3_upload = s3.Bucket(self, id=s3_bucket_name, bucket_name=s3_bucket_name,
                  #access_control=s3.BucketAccessControl.PUBLIC_READ,#不建议使用这个，这个会有list权限，下面这个没有list权限
                  public_read_access=True,
                  removal_policy=core.RemovalPolicy.DESTROY,  # TODO:  destroy for test
                  # removal_policy=core.RemovalPolicy.RETAIN
                  )
        notification = aws_s3_notifications.LambdaDestination(lambda_thum)
        s3_filter = s3.NotificationKeyFilter(suffix=".mp4")
        s3_upload.add_event_notification(s3.EventType.OBJECT_CREATED_PUT,notification,s3_filter)
        s3_upload.add_cors_rule(allowed_methods=[HttpMethods.POST,HttpMethods.PUT],allowed_origins =["*"],allowed_headers=["*"])

        '''
        #创建上传lambda
        lambda_upload = _lambda.Function(
            self, 'upload',function_name='upload',
            runtime=_lambda.Runtime.JAVA_8,
            code=_lambda.Code.from_bucket(s3.Bucket.from_bucket_name(self, "cdk-data-upload-jar", bucket_name='nowfox'),
                                          'cdk-data/fileupload.jar'),
            handler='fileupload.FileUploadFunctionHandler::handleRequest',
            timeout=Duration.minutes(1),
            memory_size=512,
            role=access_role,
        )
        lambda_upload.add_environment("bucket", s3_bucket_name)
        lambda_upload.add_environment("region", "cn-northwest-1")
        '''
        core.CfnOutput(self,"authUrl",value=base_api.url+"auth",description="authUrl")
        core.CfnOutput(self,"S3BucketName",value=s3_bucket_name,description="S3BucketName")

        # 创建API Gateway，由于需要HTTP方式，而CDK只支持REST方式，无法使用CDK创建

    def _get_UUID(self, length=3):
        uid = str(uuid.uuid4())
        return ''.join(uid.split('-'))[:length]

    def add_cors_options(self, apigw_resource):
        apigw_resource.add_method('OPTIONS', apigw.MockIntegration(
            integration_responses=[{
                'statusCode': '200',
                'responseParameters': {
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,OPTIONS'"
                }
            }
            ],
            passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
            request_templates={"application/json": "{\"statusCode\":200}"}
            ),
                                  method_responses=[{
                                      'statusCode': '200',
                                      'responseParameters': {
                                          'method.response.header.Access-Control-Allow-Headers': True,
                                          'method.response.header.Access-Control-Allow-Methods': True,
                                          'method.response.header.Access-Control-Allow-Origin': True,
                                      }
                                  }
                                  ],
                                  )