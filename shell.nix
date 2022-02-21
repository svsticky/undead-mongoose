let
  sources = import ./nix/sources.nix {};
  pkgs = import sources.nixpkgs {};

  pythonEnv = pkgs.python39.withPackages (ps: [
    ps.django_4
    ps.psycopg2
    ps.pillow
    ps.requests
    ps.sentry-sdk
    (ps.callPackage ./nix/django-constance.nix {})
    ps.gunicorn
  ]);

in
  pkgs.mkShell {
    packages = [
      # Make the Python environment available
      pythonEnv
      # Make `niv` available to manage Nix snapshots
      pkgs.niv
      pkgs.haskellPackages.dotenv
    ];
  }
