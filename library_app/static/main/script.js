function showPassword() {
    let passwordInputs = document.querySelectorAll(".password");
    let showPass = document.querySelector("#showPass");
    if (showPass.checked) {
        passwordInputs.forEach(
            (passwordInput) => (passwordInput.type = "text")
        );
        setTimeout(function () {
            showPass.checked = false;
            passwordInputs.forEach(
                (passwordInput) => (passwordInput.type = "password")
            );
        }, 750);
    } else {
        passwordInputs.forEach(
            (passwordInput) => (passwordInput.type = "password")
        );
    }
}
