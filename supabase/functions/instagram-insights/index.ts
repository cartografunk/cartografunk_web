import { corsHeaders } from '../_shared/cors.ts'

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { ...corsHeaders, 'Content-Type': 'application/json' },
})

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders })
  if (request.method !== 'GET') return json({ error: 'Method not allowed' }, 405)

  const token = Deno.env.get('META_INSTAGRAM_ACCESS_TOKEN')
  const accountId = Deno.env.get('META_INSTAGRAM_ACCOUNT_ID')
  if (!token || !accountId) return json({ error: 'Instagram insights are not configured' }, 503)

  const accountUrl = new URL(`https://graph.instagram.com/${accountId}/insights`)
  accountUrl.search = new URLSearchParams({
    metric: 'impressions,reach,profile_views', period: 'day', access_token: token,
  }).toString()
  const mediaUrl = new URL(`https://graph.instagram.com/${accountId}/media`)
  mediaUrl.search = new URLSearchParams({ fields: 'id,caption,media_type,media_url,permalink,timestamp', limit: '12', access_token: token }).toString()
  const [accountResponse, mediaResponse] = await Promise.all([fetch(accountUrl), fetch(mediaUrl)])
  if (!accountResponse.ok || !mediaResponse.ok) return json({ error: 'Meta API request failed' }, 502)
  const [account, media] = await Promise.all([accountResponse.json(), mediaResponse.json()])
  const mediaWithInsights = await Promise.all((media.data ?? []).map(async (item: { id: string }) => {
    const url = new URL(`https://graph.instagram.com/${item.id}/insights`)
    url.search = new URLSearchParams({ metric: 'engagement,impressions,reach', access_token: token }).toString()
    const response = await fetch(url)
    return { ...item, insights: response.ok ? await response.json() : { data: [] } }
  }))
  return json({ fetched_at: new Date().toISOString(), account, media: mediaWithInsights })
})
