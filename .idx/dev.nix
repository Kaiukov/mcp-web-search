# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use
  channel = "stable-23.11";  # or "unstable"
  
  # System packages you need
  packages = [
    pkgs.nodejs_20
    # You don't need to explicitly add pkgs.docker when using services.docker.enable
  ];
  
  # Enable Docker service
  services.docker.enable = true;
  
  # Environment variables if needed
  env = {
    # SOME_ENV_VAR = "hello";
  };
  
  # IDE extensions
  idx.extensions = [
    "ms-azuretools.vscode-docker"  # Docker extension for IDE support
  ];
  
  # Workspace creation and startup hooks
  idx.workspace = {
    onCreate = {
      # Commands to run when workspace is first created
    };
    onStart = {
      # Commands to run each time workspace starts
    };
  };
  
  # Preview configurations if needed
  idx.previews = {
    enable = true;
    previews = {
      # Your preview configurations
    };
  };
}