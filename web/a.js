var MAX_TRY_COUNT = 3    // 最大尝试次数
var INTERVAL_TIME = 3000  //时间间隔
var current_try_count = 1 //当前尝试次数
var pre_s3_url = 'https://dikers-html.s3.cn-northwest-1.amazonaws.com.cn/'
var vue ;
$(function(){

  vue = new Vue({
          el: '#main',
          data:{
              pageCount:0,
              thumbnail_image_url:'#'
           },methods:{
              upload_video_file:function(){
                  upload_video_file()
              }
           }
  })

});

function upload_video_file(){

    var fileChooser = document.getElementById('file-chooser');
    if(fileChooser.files == null || fileChooser.files.length ==0 ){
        alert('请先选择mp4文件')
        return ;
    }

    var file = fileChooser.files[0];
    file_name = file.name.replaceAll(' ', '_')
    //Image 的名称是视频名称加 .jpg
    var image_file_name = file_name + '.jpg'

    // 文件越大 尝试次数越多
    MAX_TRY_COUNT = MAX_TRY_COUNT + MAX_TRY_COUNT* parseInt(file.size/(1024*1024))


    //FIXME: 将URL替换成 视频上传以后生成的缩略图的URL

    //FIXME:  替换实际的图片地址 url = pre_s3_url + image_file_name
    url = pre_s3_url + 'sheep.png'   //这张图片可以测试成功
    setTimeout("get_data('"+url+"')", INTERVAL_TIME)

}


function get_data(url){

    console.log('开始下载图片  第%d次  url: ', current_try_count, url)
    $.ajax({
          async:true,
          type:"get",
          contentType : "application/json;charset=UTF-8", //类型必填
          url:url,
          complete: function(response){
            if(response.readyState == '4' && response.status == 200){
                console.log('--------------------- 图片存在')
                vue.thumbnail_image_url = url

            }else {
                console.log('--------------------- 图片不存在')
                repeat_update_image( url)
            }
          },
          error:function(response){
                //console.log('Error readyState: %d   status: %d ' , response.readyState, response.status)
          }
    })
}

function repeat_update_image( url){
    current_try_count++
    if(current_try_count > MAX_TRY_COUNT ){
        console.log('视频上传失败， 请重新上传')
        return
    }else {
        setTimeout("get_data('"+url+"')", INTERVAL_TIME)
    }

}
String.prototype.replaceAll = function (FindText, RepText) {
    var regExp = new RegExp(FindText, "g");
    return this.replace(regExp, RepText);
}