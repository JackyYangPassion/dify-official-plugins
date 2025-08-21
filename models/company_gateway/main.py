"""
Company Gateway Model Plugin Main Entry Point
"""

from dify_plugin import Plugin, DifyPluginEnv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create plugin instance
plugin = Plugin(DifyPluginEnv())

def main():
    """
    Main entry point for the plugin
    """
    logger.info("Starting Company Gateway Plugin...")
    plugin.run()

if __name__ == "__main__":
    main()
