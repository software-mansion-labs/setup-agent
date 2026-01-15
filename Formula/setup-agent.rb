class SetupAgent < Formula
    include Language::Python::Virtualenv

    desc "AI agent for installing tools and running projects."
    homepage "https://github.com/software-mansion-labs/setup-agent"
    url "https://github.com/software-mansion-labs/setup-agent/archive/refs/tags/v0.2.0.tar.gz"
    sha256 "34077fde90d7b5b7e5711a603d7a3af5dfe693ab696e68ca6fe3cfaac39d3ce7"
    license "MIT"

    depends_on "python@3.13"

    def install
        virtualenv_install_with_resources
    end

    test do
        system "#{bin}/mytool", "--version"
    end
end
