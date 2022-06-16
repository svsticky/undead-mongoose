{ python, }:

let
    version = "2.0.0";
    sha256 = "a8b2f27c69c122d2f4d801c3759761d33debf06ae9dabbab8aed82887bba3bb8";

in

python.pkgs.buildPythonPackage rec {
    pname = "mozilla-django-oidc";
    inherit version;

    src = python.pkgs.fetchPypi {
        inherit pname version sha256;
    };

    propagatedBuildInputs = [
        python.pkgs.django_4
        python.pkgs.josepy
        python.pkgs.requests
        python.pkgs.cryptography
    ];

    doCheck = false;
}