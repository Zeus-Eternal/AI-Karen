import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// This script patches the Next.js runtime to fix the clientReferenceManifest issue

function patchNextJs() {
  console.log('Patching Next.js to fix clientReferenceManifest issue...');

  // Find the Next.js installation
  const nextPath = path.join(__dirname, 'node_modules', 'next');
  if (!fs.existsSync(nextPath)) {
    console.error('Next.js not found in node_modules');
    return false;
  }

  // Create a global manifest
  const globalManifest = {
    clientModules: {},
    edgeRouters: {},
    actionIds: {},
    segmentPaths: {},
    entryCssFiles: {},
    entryJsFiles: {},
  };

  // Patch the server runtime
  const serverRuntimePath = path.join(nextPath, 'dist', 'server', 'server-base.js');
  if (fs.existsSync(serverRuntimePath)) {
    console.log('Patching server-base.js...');
    let content = fs.readFileSync(serverRuntimePath, 'utf8');
    
    // Add a check for clientReferenceManifest
    const patch = `
    // Patch for clientReferenceManifest issue
    if (!globalThis.__RSC_MANIFEST) {
      globalThis.__RSC_MANIFEST = ${JSON.stringify(globalManifest)};
    }
    `;
    
    // Insert the patch at the beginning of the file
    content = patch + content;
    fs.writeFileSync(serverRuntimePath, content);
    console.log('Patched server-base.js');
  }

  // Patch the render server
  const renderServerPath = path.join(nextPath, 'dist', 'server', 'render-server.js');
  if (fs.existsSync(renderServerPath)) {
    console.log('Patching render-server.js...');
    let content = fs.readFileSync(renderServerPath, 'utf8');
    
    // Replace the clientReferenceManifest check
    const originalCheck = 'if (!clientReferenceManifest)';
    const patchedCheck = 'if (!clientReferenceManifest) { clientReferenceManifest = globalThis.__RSC_MANIFEST || {}; }';
    
    if (content.includes(originalCheck)) {
      content = content.replace(new RegExp(originalCheck, 'g'), patchedCheck);
      fs.writeFileSync(renderServerPath, content);
      console.log('Patched render-server.js');
    }
  }

  // Patch the app router
  const appRouterPath = path.join(nextPath, 'dist', 'server', 'app-render.js');
  if (fs.existsSync(appRouterPath)) {
    console.log('Patching app-render.js...');
    let content = fs.readFileSync(appRouterPath, 'utf8');
    
    // Replace the clientReferenceManifest check
    const originalCheck = 'if (!clientReferenceManifest)';
    const patchedCheck = 'if (!clientReferenceManifest) { clientReferenceManifest = globalThis.__RSC_MANIFEST || {}; }';
    
    if (content.includes(originalCheck)) {
      content = content.replace(new RegExp(originalCheck, 'g'), patchedCheck);
      fs.writeFileSync(appRouterPath, content);
      console.log('Patched app-render.js');
    }
  }

  // Patch the app page runtime
  const appPageRuntimePath = path.join(nextPath, 'dist', 'compiled', 'next-server', 'app-page.runtime.prod.js');
  if (fs.existsSync(appPageRuntimePath)) {
    console.log('Patching app-page.runtime.prod.js...');
    let content = fs.readFileSync(appPageRuntimePath, 'utf8');
    
    // Replace the clientReferenceManifest check
    const originalCheck = 'if (!clientReferenceManifest)';
    const patchedCheck = 'if (!clientReferenceManifest) { clientReferenceManifest = globalThis.__RSC_MANIFEST || {}; }';
    
    if (content.includes(originalCheck)) {
      content = content.replace(new RegExp(originalCheck, 'g'), patchedCheck);
      fs.writeFileSync(appPageRuntimePath, content);
      console.log('Patched app-page.runtime.prod.js');
    }

    // Also fix the clientModules access
    const originalAccess = 'clientReferenceManifest.clientModules';
    const patchedAccess = '(clientReferenceManifest || globalThis.__RSC_MANIFEST || {}).clientModules';
    
    if (content.includes(originalAccess)) {
      content = content.replace(new RegExp(originalAccess, 'g'), patchedAccess);
      fs.writeFileSync(appPageRuntimePath, content);
      console.log('Fixed clientModules access in app-page.runtime.prod.js');
    }
  }

  console.log('Next.js patching completed');
  return true;
}

// Run the patch
patchNextJs();