(function(){
    var input = document.getElementById('id_password');
    var btn   = document.getElementById('toggle_password_btn');
    if (!input || !btn) return;

    btn.addEventListener('click', function () {
      var toText = input.type === 'password';
      try { input.type = toText ? 'text' : 'password'; }
      catch(e){
        var c = input.cloneNode(true);
        c.type = toText ? 'text' : 'password';
        input.parentNode.replaceChild(c, input);
        input = c;
      }
      var icon = btn.querySelector('.password-toggle-icon');
      if (icon) {
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
      }
      btn.setAttribute('aria-pressed', String(input.type === 'text'));
    });
  })();
