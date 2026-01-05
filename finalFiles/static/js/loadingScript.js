function checkFlag() {
    fetch('/check_flag')
        .then(r => r.json())
        .then(data => {
            if (data.status === "success") {
                window.location.href = data.previousPage;
            }
            else if (data.status === "failed") {
                sessionStorage.setItem("db_error", data.error);
                window.location.href = "/db_error";
            }
            else {
                setTimeout(checkFlag, 2000);
            }
        });
}

window.onload = checkFlag;
