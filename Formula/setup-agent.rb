class SetupAgent < Formula
  include Language::Python::Virtualenv

  desc "AI agent for installing tools and running projects."
  homepage "https://github.com/software-mansion-labs/setup-agent"
  url "https://pypi.io/packages/source/s/setup-agent/setup_agent-${VERSION}.tar.gz"
  sha256 "d57dc0ea8b2342cef1d037302fa8554b081e66bcc3af75371057f13b5d2c8a57"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/setup-agent", "--version"
  end
end
