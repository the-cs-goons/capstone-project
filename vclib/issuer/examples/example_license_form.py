html_license_form = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Demonstration Issuer Form</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- Bootstrap -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <!-- You can add your styles and scripts here -->
    <script>
        function submit() {
            axios.post(window.location.href , {
                license_no: +document.getElementById('license_no').value,
                date_of_birth: document.getElementById('date_of_birth').value,
            });
            window.location.href = 'https://localhost:8080/credentials';
        }
    </script>
</head>

<header style="margin: 3em;">
    <nav class="navbar" style=>
        <h1>Example Driver's License Issuer Website</h1>
    </nav>
    <p>
        This is an example form that a Credential issuer might provide to a Holder. <br>
        In the real world, this could be a multi-step process of getting the Holder to log in. <br>
        This is a simple example form that matches the inputs given below to some mocked data. <br>
        If the inputs match, the user will be successfully redirected back to their wallet with a brand new credential!
    </p>
</header>
<body>
    <main role="main" style="margin: 3em;">
        <div class="oauth" id="oauth">
                <h2>Driver's License Request Form</h2>
                <div id="license_no-wrapper" class="input-label-wrapper mb-3">
                    <label for="license_no" class="form-label">License Number</label>
                    <input name="license_no" id="license_no" class="form-control" type="number" placeholder="00000">
                </div>
                <div id="date_of_birth-wrapper" class="input-label-wrapper mb-3">
                    <label for="date_of_birth" class="form-label">Date of Birth</label>
                    <input name="date_of_birth" id="date_of_birth" class="form-control" type="date" placeholder="01/01/1970">
                </div>
                <button id="auth-button" class="btn btn-primary" onclick="submit()">Authorize</button>
        </div>
    </main>
</body>

"""
