$(function(){
    var submitTxt;
    $('#id_audio').fileupload({
        url: '/speech/ajax_audio',
        dataType: 'json',
        add: function(e, data) {
            var valid = true;
            $.each(data.files, function(i, file){
                if (!(/.(ogg|mp3)$/.test(file.name) || /audio\//.test(file.type))) {
                    valid = false;
                }
            });
            if (!valid) {
                $('#id_audio').closest('div.control-group').addClass('error');
                $('#id_audio').closest('div.control-group').find('.help-inline').html('Please pick an audio file');
                return;
            }
            $('#id_audio').prop('disabled', true).parent().addClass('disabled');
            submitTxt = $('#speech_submit').val();
            $('#speech_submit').prop('disabled', true).val('Uploading audio...');
            $('.progress-result').hide();
            $('.progress').show();
            data.submit();
        },
        progressall: function(e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('.progress .bar').css( 'width', progress + '%' );
        },
        always: function(e, data) {
            $('#speech_submit').prop('disabled', false).val(submitTxt);
            $('.progress').hide();
        },
        show_failure: function(msg) {
            $('.progress-result').html('Something went wrong: ' + msg).show();
            $('#id_audio').prop('disabled', false).parent().removeClass('disabled');
        },
        fail: function(e, data) {
            return this.show_failure(data.errorThrown);
        },
        done: function(e, data) {
            if (data.result.error) {
                return this.show_failure(data.result.error);
            }
            var client_filename = data.files[0].name,
                server_filename = data.result.filename;
            $('.progress-result').html('Uploaded: ' + client_filename).show();
            $('#id_audio_filename').val(server_filename);
        }
    });
});

