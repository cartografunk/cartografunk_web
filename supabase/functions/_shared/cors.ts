export const corsHeaders = {
  'Access-Control-Allow-Origin': Deno.env.get('MEDIA_KIT_ORIGIN') ?? 'https://cartografunk.com',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
}
