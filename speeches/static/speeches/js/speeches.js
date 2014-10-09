$(function() {
    sayit_enable_date_pickers();
    sayit_ajax_file_uploads();
    sayit_link_prev_next_keyboard();
    setup_unimportant_sections();
    hide_new_speaker_controls();

    var audios = $('audio').not('.audio-small');
    if (audios.mediaelementplayer) {
        audios.mediaelementplayer();
    }
});

function sayit_enable_date_pickers() {
    var datepickers = $(".fdatepicker"),
        l = datepickers.length;

    if (!l || !datepickers.fdatepicker) {
        return;
    }

    datepickers.fdatepicker({
        format:datepickers.attr('datepicker-format'),
        weekStart: 1
    })

    // Make the speech end date the same as the start the first time people
    // enter something in the start
    $("#id_start_date").one("changeDate", function(e) {
        dateString = $("#id_start_date").val();
        $("#id_end_date").val(dateString);
    });
}

function sayit_ajax_file_uploads() {
    var submitTxt,
        audio = $('#id_audio'),
        l = audio.length;

    if (!l) {
        return;
    }

    audio.fileupload({
        url: '/speech/ajax_audio',
        dataType: 'json',
        add: function(e, data) {
            var valid = true;
            $.each(data.files, function(i, file) {
                if (!(/.(ogg|mp3|wav|3gp)$/.test(file.name) || /audio\//.test(file.type))) {
                    valid = false;
                }
            });
            if (!valid) {
                audio.closest('div.row').addClass('error');
                audio.closest('div.row').find('.help-inline').html('Please pick an audio file');
                return;
            }
            audio.prop('disabled', true).parent().addClass('disabled');
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
            audio.prop('disabled', false).parent().removeClass('disabled');
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
}

function sayit_link_prev_next_keyboard() {
    var prev = $('link[rel=prev]'),
        next = $('link[rel=next]');
    if (prev.length) {
        $(document).keyup(function(e) {
            if (e.target === document.body && e.which == 74) {
                window.location = prev.attr('href');
            }
        });
    }
    if (next.length) {
        $(document).keyup(function(e) {
            if (e.target === document.body && e.which == 75) {
                window.location = next.attr('href');
            }
        });
    }
}

function setup_unimportant_sections() {
    $('.unimportant-form-section-header').on('click', function(){
        $(this).toggleClass('collapsed').next().toggle();
    }).addClass('collapsed');
    $('.unimportant-form-section').hide().has('.error').show().prev().removeClass('collapsed');
}

function hide_new_speaker_controls() {
    var new_speaker_controls = $('#id_new_speaker_controls');
    $('input[name="action"][value="Reassign"]').parent().after(new_speaker_controls);
    $('input[name="action"]').change(
        function() {
            var i = $('input[name="action"]:checked').val();
            if (i == 'Reassign') {
                new_speaker_controls.show();
            } else {
                new_speaker_controls.hide();
            }
        }
    ).change();
}
