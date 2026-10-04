// Stub the Spotify Web Playback SDK entry point before it loads.
//
// The SDK throws unless `window.onSpotifyWebPlaybackSDKReady` exists; it only
// signals that a listener is present. Kept as an external file (not inline) so
// the app works under a CSP with `script-src 'self'` and no `unsafe-inline`.
window.onSpotifyWebPlaybackSDKReady = function () {};
