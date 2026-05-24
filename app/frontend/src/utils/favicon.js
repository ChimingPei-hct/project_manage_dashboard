/** 运行时 favicon 注入。
 *
 * 每个 PDT 实例的图标不同,无法在 index.html 静态写 <link rel="icon">,
 * 必须在 PDT 配置加载后动态注入/替换。详见 design/13 §6.0。
 */

const LINK_ID = 'pmd-favicon'

export function setFavicon(url) {
  let link = document.getElementById(LINK_ID)
  if (!url) {
    if (link) link.remove()
    return
  }
  if (!link) {
    link = document.createElement('link')
    link.id = LINK_ID
    link.rel = 'icon'
    document.head.appendChild(link)
  }
  // SVG 与 PNG 都让浏览器根据扩展名自行处理
  link.href = url
}

export function iconUrlOf(pdt) {
  const rel = pdt?.icon
  if (!rel) return ''
  return rel.startsWith('/') ? rel : `/${rel}`
}
