# This file defines a package definition for `django-constance`, which is not
# in Nixpkgs. It takes a Python version to build for:
{ python, }:

let
  # This version and SHA256 should match one of the releases here:
  # https://pypi.org/project/django-constance/
  version = "2.8.0";
  sha256 = "0a492454acc78799ce7b9f7a28a00c53427d513f34f8bf6fdc90a46d8864b2af";

  # The default definition of `django-picklefield` builds for Django 2, which
  # causes a conflict if you want a different Django version.
  # For the upstream definition, see:
  # https://github.com/NixOS/nixpkgs/blob/master/pkgs/development/python-modules/django-picklefield/default.nix
  fixed-picklefield = python.pkgs.django-picklefield.overridePythonAttrs (old: {
    # Pass Django 4 instead of Django 2 to the build:
    propagatedBuildInputs = [ python.pkgs.django_4 ];
    # If you override this version the test dependencies also need to be
    # updated, or you disable the tests. The latter is easier, so do that:
    doCheck = false;
  });

in

python.pkgs.buildPythonPackage rec {
  pname = "django-constance";
  inherit version;

  src = python.pkgs.fetchPypi {
    inherit pname version sha256;
  };

  # Pass the updated dependencies:
  propagatedBuildInputs = [
    python.pkgs.django_4
    fixed-picklefield
  ];

  # No tests here either:
  doCheck = false;
}
