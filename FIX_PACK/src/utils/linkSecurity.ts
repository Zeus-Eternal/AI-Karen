'use client';

import { validateUrl } from '@/components/security/SecureLink';

export interface LinkSecurityReport {
  totalLinks: number;
  secureLinks: number;
  insecureLinks: number;
  violations: Array<{
    href: string;
    reason: string;
    location: string;
  }>;
}

/**
 * Scans a React component tree for insecure links
 */
export const scanComponentForInsecureLinks = (
  componentSource: string,
  componentName: string
): LinkSecurityReport => {
  const report: LinkSecurityReport = {
    totalLinks: 0,
    secureLinks: 0,
    insecureLinks: 0,
    violations: []
  };

  // Regex patterns to find different types of links
  const patterns = [
    // JSX href attributes
    /href\s*=\s*["']([^"']+)["']/g,
    // Template literals in href
    /href\s*=\s*{`([^`]+)`}/g,
    // Variable references in href
    /href\s*=\s*{([^}]+)}/g,
    // window.open calls
    /window\.open\s*\(\s*["']([^"']+)["']/g,
    // location.href assignments
    /location\.href\s*=\s*["']([^"']+)["']/g
  ];

  patterns.forEach((pattern, patternIndex) => {
    let match;
    while ((match = pattern.exec(componentSource)) !== null) {
      const href = match[1];
      report.totalLinks++;

      // Skip dynamic expressions for now (would need AST parsing)
      if (patternIndex === 2 && !href.startsWith('http') && !href.startsWith('/')) {
        continue;
      }

      const validation = validateUrl(href);
      
      if (!validation.isSafe || !validation.isValid) {
        report.insecureLinks++;
        report.violations.push({
          href,
          reason: validation.reason,
          location: `${componentName}:${getLineNumber(componentSource, match.index)}`
        });
      } else {
        report.secureLinks++;
      }
    }
  });

  return report;
};

/**
 * Gets the line number for a given character index in source code
 */
const getLineNumber = (source: string, index: number): number => {
  return source.substring(0, index).split('\n').length;
};

/**
 * Generates secure link replacement suggestions
 */
export const generateSecureLinkFixes = (violations: LinkSecurityReport['violations']): string[] => {
  return violations.map(violation => {
    const { href, reason, location } = violation;
    
    if (reason.includes('Dangerous protocol')) {
      return `${location}: Replace dangerous URL "${href}" with a safe alternative or remove the link`;
    }
    
    if (reason.includes('Invalid URL')) {
      return `${location}: Fix malformed URL "${href}" or use a relative path`;
    }
    
    if (reason.includes('Unsupported protocol')) {
      return `${location}: Replace unsupported protocol in "${href}" with http/https`;
    }
    
    return `${location}: Review and fix insecure link "${href}" - ${reason}`;
  });
};

/**
 * Automatically fixes common link security issues in component source
 */
export const autoFixLinkSecurity = (componentSource: string): {
  fixedSource: string;
  changes: string[];
} => {
  let fixedSource = componentSource;
  const changes: string[] = [];

  // Fix 1: Add rel="noopener noreferrer" to external links missing it
  const externalLinkPattern = /(<a[^>]+href\s*=\s*["']https?:\/\/[^"']+["'][^>]*?)(?!.*rel\s*=)([^>]*>)/g;
  fixedSource = fixedSource.replace(externalLinkPattern, (match, beforeRel, afterRel) => {
    changes.push('Added rel="noopener noreferrer" to external link');
    return `${beforeRel} rel="noopener noreferrer"${afterRel}`;
  });

  // Fix 2: Add target="_blank" to external links missing it
  const externalLinkNoTargetPattern = /(<a[^>]+href\s*=\s*["']https?:\/\/[^"']+["'][^>]*?)(?!.*target\s*=)([^>]*>)/g;
  fixedSource = fixedSource.replace(externalLinkNoTargetPattern, (match, beforeTarget, afterTarget) => {
    changes.push('Added target="_blank" to external link');
    return `${beforeTarget} target="_blank"${afterTarget}`;
  });

  // Fix 3: Remove dangerous javascript: links
  const javascriptLinkPattern = /href\s*=\s*["']javascript:[^"']*["']/g;
  fixedSource = fixedSource.replace(javascriptLinkPattern, 'href="#"');
  if (javascriptLinkPattern.test(componentSource)) {
    changes.push('Removed dangerous javascript: URLs');
  }

  // Fix 4: Replace SecureLink component usage
  const basicLinkPattern = /<a\s+href\s*=\s*["']([^"']+)["']([^>]*)>/g;
  fixedSource = fixedSource.replace(basicLinkPattern, (match, href, attributes) => {
    // Only replace if it's an external link and doesn't already use SecureLink
    if (href.startsWith('http') && !componentSource.includes('SecureLink')) {
      changes.push(`Replaced <a> with <SecureLink> for ${href}`);
      return `<SecureLink href="${href}"${attributes}>`;
    }
    return match;
  });

  // Add SecureLink import if we made replacements
  if (changes.some(change => change.includes('SecureLink'))) {
    if (!fixedSource.includes('SecureLink')) {
      const importPattern = /^(import.*from\s+['"][^'"]*['"];?\s*\n)/m;
      const importMatch = fixedSource.match(importPattern);
      
      if (importMatch) {
        const insertIndex = importMatch.index! + importMatch[0].length;
        fixedSource = 
          fixedSource.slice(0, insertIndex) +
          "import { SecureLink } from '@/components/security/SecureLink';\n" +
          fixedSource.slice(insertIndex);
        changes.push('Added SecureLink import');
      }
    }
  }

  return { fixedSource, changes };
};

/**
 * Validates all links in a component and returns a security report
 */
export const auditComponentLinkSecurity = (
  componentSource: string,
  componentName: string
): {
  report: LinkSecurityReport;
  fixes: string[];
  autoFixResult: { fixedSource: string; changes: string[] };
} => {
  const report = scanComponentForInsecureLinks(componentSource, componentName);
  const fixes = generateSecureLinkFixes(report.violations);
  const autoFixResult = autoFixLinkSecurity(componentSource);

  return {
    report,
    fixes,
    autoFixResult
  };
};

/**
 * Batch audit multiple components
 */
export const batchAuditLinkSecurity = (
  components: Array<{ source: string; name: string }>
): {
  overallReport: LinkSecurityReport;
  componentReports: Array<{
    name: string;
    report: LinkSecurityReport;
    fixes: string[];
  }>;
} => {
  const overallReport: LinkSecurityReport = {
    totalLinks: 0,
    secureLinks: 0,
    insecureLinks: 0,
    violations: []
  };

  const componentReports = components.map(({ source, name }) => {
    const audit = auditComponentLinkSecurity(source, name);
    
    // Aggregate to overall report
    overallReport.totalLinks += audit.report.totalLinks;
    overallReport.secureLinks += audit.report.secureLinks;
    overallReport.insecureLinks += audit.report.insecureLinks;
    overallReport.violations.push(...audit.report.violations);

    return {
      name,
      report: audit.report,
      fixes: audit.fixes
    };
  });

  return {
    overallReport,
    componentReports
  };
};

export default {
  scanComponentForInsecureLinks,
  generateSecureLinkFixes,
  autoFixLinkSecurity,
  auditComponentLinkSecurity,
  batchAuditLinkSecurity
};