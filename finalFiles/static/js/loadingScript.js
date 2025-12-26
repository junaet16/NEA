function checkFlag() {
    fetch('/check_flag')
        .then(response => response.json())
        .then(data => {
            if (data.databaseCreated) {
                console.log(data.previousPage)
                window.location.href = data.previousPage;
            } else {
                setTimeout(checkFlag, 2000);
            }
        });
}

window.onload = checkFlag;