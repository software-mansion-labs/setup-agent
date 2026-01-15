class SetupAgent < Formula
  include Language::Python::Virtualenv

  desc "AI agent for installing tools and running projects."
  homepage "https://github.com/software-mansion-labs/setup-agent"
  url "https://pypi.io/packages/source/s/setup-agent/setup_agent-0.2.6.tar.gz"
  sha256 "48dae33c9c1e23444a95a1ff558b294c63fda08b70d03a093217ec92f24f41d1"
  license "MIT"

  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/setup-agent", "--version"
  end
end
