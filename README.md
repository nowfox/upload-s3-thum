# 项目介绍

通过网页直接上传文件(.mp4)到S3，触发Lambda函数，生成一张截图。
网页上传文件所需的**访问密钥 ID(Access key ID，简称AK)**和**私有访问密钥(Secret access key，简称SK)**从API Gateway获取，API Gateway调用Lambda函数获取Session Token，网页使用Session Token来上传文件。


# 步骤

1. 下载项目到本地
2. 登录AWS控制台创建用户，访问类型需要选中**编程访问**，所需权限需要包含以下内容，然后记录下AKSK。
```
"Action": [     
                "sts:GetSessionToken",
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObjectTagging",
                "s3:DeleteObject",
                "s3:PutObjectAcl"
            ]
```
3. 修改[cdk/constant.py](cdk/constant.py)中的AK、SK为第2步生成的值
4. 使用cdk部署，记录下authUrl和S3BucketName
5. 修改[upload.html](./upload.html)中的authUrl、bucketName值。
6. 然后再浏览器中打开upload.html即可上传文件和生成缩略图