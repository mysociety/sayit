$(function(){
    var submitTxt;

    // Make them answer an Audio/Text question first if it's a brand new speech
    if($("p.lead").hasClass("add-speech") && $("ul.errorlist").length == 0) {
        $("form#speech-form").hide();
        $("p#question").show();
        // Click handlers for the options
        $("a#audio-link").click(function(){
            selectFormOption("#id_text_controls");
            return false;
        });
        $("a#text-link").click(function(){
            selectFormOption("#id_audio_controls");
            return false;
        }); 
        $("a#both-link").click(function(){
            selectFormOption();
            return false;
        });
    }
    else {
        enableDatePickers();
    } 

    function selectFormOption(selectorsToHide) {
        $("p#question").hide();
        $("form#speech-form").show();
        if(typeof selectorsToHide !== "undefined") {
            $(selectorsToHide).hide()
        }
        enableDatePickers();
    }

    function enableDatePickers(){
        // Datepickers
        $("input#id_start_0, input#id_end_0").datepicker({
            format:'dd/mm/yyyy',
            weekStart: 1,
            autoclose: true,        
        })

        // Placeholders for dates
        $("input#id_start_0, input#id_end_0").attr("placeholder", "dd/mm/yyyy");

        // Add placeholder attributes to times too
        $("input#id_start_1, input#id_end_1").attr("placeholder", "hh:mm");

        // Make the end the same as the start the first time people
        // enter something in the start
        $("#id_start_0").one("changeDate", function(e) {
            dateString = $("#id_start_0").val();
            $("#id_end_0").val(dateString);
            $("#id_end_0").datepicker("setStartDate", dateString);
        });

        // Make the times auto-fill with 00:00 if they're empty, because
        // Django doesn't default them to anything and throws a validation error
        $("input#id_start_0").on("changeDate", function(e) {
            $time = $("input#id_start_1")
            if( $time.val() == "" ){
                $time.val("00:00")
            }
        });
        $("input#id_end_0").on("changeDate", function(e) {
            $time = $("input#id_end_1")
            if( $time.val() == "" ){
                $time.val("00:00")
            }
        });
    }

    // Ajax file uploads
    $('#id_audio').fileupload({
        url: '/speech/ajax_audio',
        dataType: 'json',
        add: function(e, data) {
            var valid = true;
            $.each(data.files, function(i, file){
                if (!(/.(ogg|mp3|wav|3gp)$/.test(file.name) || /audio\//.test(file.type))) {
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

