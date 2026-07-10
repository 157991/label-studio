/**
 * PostCSS plugin to add lsf- prefix to class selectors in .prefix.css files.
 * 
 * This handles the case where .prefix.css files are imported globally
 * (not as CSS Modules), so css-loader's getLocalIdent never runs.
 */
module.exports = (opts = {}) => {
  const prefix = opts.prefix || 'lsf-';

  return {
    postcssPlugin: 'postcss-prefix-lsf',
    Once(root) {
      // Only process .prefix.css files
      const sourcePath = root.source?.input?.file || '';
      if (!sourcePath.endsWith('.prefix.css')) return;

      root.walkRules((rule) => {
        // Skip keyframes, font-face, etc.
        if (rule.parent && rule.parent.type === 'atrule' && 
            ['keyframes', '-webkit-keyframes', 'font-face'].includes(rule.parent.name)) {
          return;
        }

        rule.selectors = rule.selectors.map((selector) => {
          // Don't prefix already-prefixed selectors
          if (selector.includes(prefix)) return selector;
          // Don't prefix ant- classes (ant design)
          if (selector.includes('.ant-')) return selector;
          // Don't prefix HTML tag selectors without class
          if (!selector.includes('.')) return selector;

          // Prefix all class selectors in the selector string
          // Match .class-name and replace with .prefixclass-name
          return selector.replace(/\.([a-zA-Z_][a-zA-Z0-9_-]*)/g, (match, className) => {
            // Skip if already prefixed
            if (className.startsWith(prefix.replace('-', ''))) return match;
            // Skip ant classes
            if (className.startsWith('ant-')) return match;
            return `.${prefix}${className}`;
          });
        });
      });
    },
  };
};

module.exports.postcss = true;
