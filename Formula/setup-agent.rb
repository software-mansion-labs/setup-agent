class SetupAgent < Formula
  include Language::Python::Virtualenv

  desc "AI agent for installing tools and running projects."
  homepage "https://github.com/software-mansion-labs/setup-agent"
  url "https://pypi.io/packages/source/s/setup-agent/setup_agent-#{version}.tar.gz"
  sha256 "42c25fe47bffe4b0c7281ea38ae880e6f3eb783063dff1d40233cd2bc1cb0281"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/setup-agent", "--version"
  end
end
