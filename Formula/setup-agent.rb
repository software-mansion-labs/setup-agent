class SetupAgent < Formula
  include Language::Python::Virtualenv

  desc "AI agent for installing tools and running projects."
  homepage "https://github.com/software-mansion-labs/setup-agent"
  url "https://github.com/software-mansion-labs/setup-agent/archive/refs/tags/v0.2.0.tar.gz"
  sha256 "0019dfc4b32d63c1392aa264aed2253c1e0c2fb09216f8e2cc269bbfb8bb49b5"
  license "MIT"

  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
  end
end