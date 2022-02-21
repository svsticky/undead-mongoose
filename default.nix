let
  sources = import ./nix/sources.nix {};
  pkgs = import sources.nixpkgs {};

  pythonEnv = pkgs.python39.withPackages (ps: [
    ps.django_4
    ps.psycopg2
    ps.pillow
    ps.requests
    ps.sentry-sdk
  ]);

in
  {
    # Make the Python environment available
    inherit pythonEnv;
    # Make `niv` available to manage Nix snapshots
    inherit (pkgs) niv;
  }
