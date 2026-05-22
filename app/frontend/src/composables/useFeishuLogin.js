/**
 * 飞书 OAuth 前端流程(对接 design/11 §6.1)
 *
 * 1. handleCallbackIfPresent():页面挂载时调用。若当前 URL 是 /feishu/callback?code=...
 *    则把 code POST 给后端,后端写 cookie 返回用户信息,然后清掉路径回到 /。
 * 2. startLogin():跳到飞书授权页。
 */

import { api } from '../api/client.js'

const CALLBACK_PATH = '/feishu/callback'

export async function handleCallbackIfPresent() {
  if (window.location.pathname !== CALLBACK_PATH) return null
  const sp = new URLSearchParams(window.location.search)
  const code = sp.get('code')
  if (!code) {
    // 用户拒绝授权或飞书直接 redirect 没 code,回首页
    window.history.replaceState({}, '', '/')
    return null
  }
  try {
    const data = await api.post('/api/feishu/callback', { code })
    // 登录成功:清掉 query,回到首页(不保留 ?view= 因为登录前没保存)
    window.history.replaceState({}, '', '/')
    return data
  } catch (e) {
    // 失败也清 query,但保留报错给上层
    window.history.replaceState({}, '', '/')
    throw e
  }
}

export async function startLogin() {
  const redirect = `${window.location.origin}${CALLBACK_PATH}`
  const { login_url } = await api.get(`/api/feishu/login_url?redirect_uri=${encodeURIComponent(redirect)}`)
  window.location.href = login_url
}
