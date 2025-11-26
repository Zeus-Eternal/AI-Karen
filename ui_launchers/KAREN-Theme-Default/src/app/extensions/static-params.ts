/**
 * Static params for extension pages
 */

export function generateStaticParams() {
  // Return sample slug paths for static generation
  return [
    { slug: ['marketplace'] },
    { slug: ['installed'] },
    { slug: ['settings'] },
    { slug: ['developer'] },
    { slug: ['marketplace', 'detail'] },
    { slug: ['marketplace', 'install'] },
  ];
}