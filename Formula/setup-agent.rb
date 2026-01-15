class SetupAgent < Formula
  include Language::Python::Virtualenv

  desc "AI agent for installing tools and running projects."
  homepage "https://github.com/software-mansion-labs/setup-agent"
  url "https://pypi.io/packages/source/s/setup-agent/setup_agent-0.2.5.tar.gz"
  sha256 "55867bf9ce62dc253ab2ba92082846c43d66c5a5d44529e0e28c754be20218d7"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/setup-agent", "--version"
  end
end
