$(document).ready(function() {
  $("#opsearch").click(function() {
    var name = $("#opnamesearch").val();
    var url = "/mcuuid/"+name;
    var response = getURL(url);
    if ( response === '' ) {
      $('#opsearchstatus').html('<div class="alert alert-danger" role="alert">User Not Found</div>');
    } else {
      var json = JSON.parse(response);
      $('#opsearchstatus').html('<div class="alert alert-success" role="alert">User '+json['name']+' found with id: '+json['id']+'</div>');
      $('#opusers').append($('<option selected value="'+json['name']+'">'+json['name']+'-'+json['id']+'</option>'));
      $('#whitelistusers').append($('<option selected value="'+json['name']+'">'+json['name']+'-'+json['id']+'</option>'));
    }
  });
  $('#opnamesearch').keypress(function(e){
    if(e.which == 13){//Enter key pressed
      $('#opsearch').click();//Trigger search button click event
    }
  });
  $("#whitelistsearch").click(function() {
    var name = $("#whitelistnamesearch").val();
    var url = "/mcuuid/"+name;
    var response = getURL(url);
    if ( response === '' ) {
      $('#whitelistsearchstatus').html('<div class="alert alert-danger" role="alert">User Not Found</div>');
    } else {
      var json = JSON.parse(response);
      $('#whitelistsearchstatus').html('<div class="alert alert-success" role="alert">User '+json['name']+' found with id: '+json['id']+'</div>');
      $('#whitelistusers').append($('<option selected value="'+json['name']+'">'+json['name']+'-'+json['id']+'</option>'));
    }
  });
  $('#whitelistnamesearch').keypress(function(e) {
    if(e.which == 13){ //Enter key pressed
      $('#whitelistsearch').click(); //Trigger search button click event
    }
  });
  $("#create").click(function() {
    $('#createstatus').html('<img src="/static/giphy.gif" height="50">');
    var opusers = $('#opusers').val();
    var data="opusers="+opusers
    var whitelistusers = $('#whitelistusers').val();
    data=data+"&whitelistusers="+whitelistusers
    var version = $('#version').val()
    data=data+"&version="+version
    var servername = $('#servername').val()
    data=data+'&servername='+servername
    var serverrunner = $('#serverrunner').val()
    data=data+'&serverrunner='+serverrunner
    var port = $('#port').val()
    data=data+'&port='+port
    var gamemode = $('#gamemode').val()
    data=data+'&gamemode='+gamemode
    $.post("/newmcserver", data=data)
    .done(function() {
      $('#createstatus').html('<div class="alert alert-success" role="alert">Server Created Successfully.</div>');
    })
    .fail(function(data) {
      var result = data.responseJSON;
      $('#createstatus').html('<div class="alert alert-danger" role="alert">Server Creation Failed. '+result['Error']+'</div>');
    })
  });
  $('#servername').keypress(function(e) {
    if(e.which == 13){ //Enter key pressed
      $('#create').click(); //Trigger search button click event
    }
  });
  $('#servername').keyup(function() {
    var servername = $('#servername').val();
    if ( !servername.match(/^[a-zA-Z0-9]+[a-zA-Z0-9_-]*$/)) {
      $('#servername_info').removeClass('text-success').addClass('text-danger');
      $('#create').prop("disabled", true);
    } else {
      $('#servername_info').removeClass('text-danger').addClass('text-success');
      $('#create').prop("disabled", false);
    }
  });
  $('#deleteModal').on('show.bs.modal', function(e) {
    $(this).find('#formdelete').attr('action', $(e.relatedTarget).data('href'));
  });
  $('#alertclose').click(function() {
    $('.alert').fadeTo(0, 500).slideUp(500, function(){
      $('.alert').slideUp(500);
    });
  });
  var xhr = new XMLHttpRequest();
  $('#logsModal').on('show.bs.modal', function(e) {
    var output = document.getElementById('output');
    xhr.open('GET', '/log_stream/'+$(e.relatedTarget).data('href'), true);
    xhr.send();
    setInterval(function() {
      output.textContent = xhr.responseText;
    }, 500);
  });
  $('#logsModalClose').click(function() {
    xhr.abort();
  });
  $('#generateqrcode').click(function(){
    //TODO: Fix useremailid
    var useremailid = $('#useremailid').text();
    var response = JSON.parse(getURL('/token'))
    $('#qrcode').qrcode("otpauth://totp/mcshop:"+useremailid+"?secret="+response.SecretCode+"&issuer=mcshop");
    $('#tokenstring').html( response.SecretCode )
  });
  $('input[type=password]').keyup(function() {

    //check if they match
    if ($('#newpwone').val() === $('#newpwtwo').val()) {
      $('#match').removeClass('text-danger').addClass('text-success');
      $('#changepassword').prop("disabled", false);
    } else {
      $('#match').removeClass('text-success').addClass('text-danger');
      $('#changepassword').prop("disabled", true);
    }

    var pswd = $('#newpwone').val();

    if (pswd != null) {
      //text-successate the length
      if ( pswd.length < 8 ) {
        $('#length').removeClass('text-success').addClass('text-danger');
        $('#changepassword').prop("disabled", true);
      } else {
        $('#length').removeClass('text-danger').addClass('text-success');
      }

      //text-successate letter
      if ( pswd.match(/[A-z]/) ) {
        $('#letter').removeClass('text-danger').addClass('text-success');
      } else {
        $('#letter').removeClass('text-success').addClass('text-danger');
        $('#changepassword').prop("disabled", true);
      }

      //text-successate capital letter
      if ( pswd.match(/[A-Z]/) ) {
        $('#capital').removeClass('text-danger').addClass('text-success');
      } else {
        $('#capital').removeClass('text-success').addClass('text-danger');
        $('#changepassword').prop("disabled", true);
      }

      //text-successate number
      if ( pswd.match(/\d/) ) {
        $('#number').removeClass('text-danger').addClass('text-success');
      } else {
        $('#number').removeClass('text-success').addClass('text-danger');
        $('#changepassword').prop("disabled", true);
      }

      //text-successate symbol
      if ( pswd.match(/[$-/:-?{-~!"^_`\[\]]/) ) {
        $('#symbol').removeClass('text-danger').addClass('text-success');
      } else {
        $('#symbol').removeClass('text-success').addClass('text-danger');
        $('#changepassword').prop("disabled", true);
      }
    }

    }).focus(function() {
      $('#pswd_info').show();
    }).blur(function() {
      $('#pswd_info').hide();
  });
});

function getURL(url){
    return $.ajax({
        type: "GET",
        url: url,
        cache: false,
        async: false
    }).responseText;
}
