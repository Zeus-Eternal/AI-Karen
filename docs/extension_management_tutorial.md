# Extension Management Tutorial

This tutorial walks through enabling and managing extensions in the AI Karen web UI.

1. **Enable the feature flag**
   
   Set the environment variable `KAREN_ENABLE_EXTENSIONS=true` before starting the web UI. This will replace the plugin sidebar with the new Extension Manager.

2. **Browse extensions**
   
   Open the navigation sidebar and select **Extensions**. Categories and breadcrumbs help you drill down to specific providers, models and settings.

3. **Install from marketplace**
   
   Use the "Install" button on any available extension. Dependencies are resolved automatically and the extension becomes active when installation completes.

4. **Configure providers**
   
   Select an installed extension to view available providers. Adjust settings such as API keys, model parameters or audio options. Changes are applied immediately.

5. **Monitor health**
   
   The stats panel shows CPU, memory and error information. Use this to ensure extensions are running correctly.

6. **Disable or remove**
   
   From the extension details page you can disable or completely remove an extension. This triggers shutdown hooks and cleans up any resources.

