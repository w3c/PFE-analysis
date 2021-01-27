Author: Garret Rieger  
Date: November 16th, 2020  

# Current Patch Subset Protocol Design

The existing
[patch subset protocol design](https://github.com/w3c/PFE-analysis/blob/master/design/patch_subset_protocol.md)
was not designed with backwards compatibility in mind. It currently uses POST for all requests. The use
of POST requests makes it difficult to allow a patch/subset request to be correctly handled by a legacy
server which does not understand the patch/subset protocol.

The remainder of this doc is a proposal for modifying the patch subset protocol to allow for backwards
compatibility. Here backwards compatibility means:

*  A PFE aware client can send a PFE request to a legacy HTTP server (that is a server which does not
   have an implementation of the patch/subset protocol) and still get a valid response back.
*  The backwards compatibility mechanism should also allow the PFE aware client to fall back to using
   HTTP range requests for PFE as long as the font on the legacy server has been appropriately
   formatted.
   
# Proposal

## On Naming

The parameter and header names used in this doc are not meant to be final, these are just placeholder names to illustrate the general approach.

## Font Face CSS

```css
@font-face {
  src: url(https://foo.bar/the_font.woff2) format('woff2');
  src: url(https://foo.bar/the_font.ttf) format(truetype supports incremental);
}
```

<table>
    <tr>
        <th></th><th>Legacy Client</th><th>PFE Client</th>
    </tr>
    <tr>
        <th>Legacy Server</th>
        <td>
            <ul>
                <li>Client ignores the incremental url and requests the next in the chain.</li>
                <li>Legacy server handles the normal static file request.</li>
            </ul>
        </td>
        <td>
            <ul>
                <li>Client sends PFE request to incremental URL.</li>
                <li>Request is formulated so that to a legacy server it looks like a standard
                    static file request.</li>
                <li>Response back to client looks like a normal static file, so client switches to
                    using HTTP ranges for incremental transfer (if font is TTF/OTF and glyph table
                    is at the end).</li>
                <li>The client can identify the response as a static file by inspecting the first 4 bytes
                    of the response which will be 'OTTO' for an opentype file, or 0x00010000 for a truetype
                    file.</li>
            </ul>
        </td>
    </tr>
    <tr>
        <th>Patch/Subset Server</th>
        <td>
            <ul>
                <li>Client ignores the incremental url and requests the next in the chain.</li>
                <li>Request is missing PFE parameters so the patch/subset server handles it
                    as a normal static file request.</li>
            </ul>
        </td>
        <td>
            <ul>
                <li>Client sends request with patch/subset parameters.</li>
                <li>Server recognizes it and sends appropriate response using patch/subset
                    protocol.</li>
                <li>Client identifies the response as coming from an incremental transfer capable server
                    by inspecting the first 4 bytes of the response (identifying value TBD).</li>
                <li>Further enrichment requests are sent using non-backwards compatible patch/subset
                    specific protocol.</li>
            </ul>
        </td>
    </tr>
</table>

## Initial Request Format

### Option 1 - GET with parameters in the query string

`GET /the/font.ttf?codepoints=<bas64 encoded set>&accept_patch=<list of patch formats>`

#### Cacheability:

*  Legacy Server: server can possibly be configured to ignore the query parameters for caching
   purposes, but this may not be default behaviour.
*  Patch/Subset Server: server could cache the response using the codepoint set in the key. Can be
   served with public caching enabled since the query string uniquely identifies the response.

#### Pros:

*  Doesn’t rely on custom headers, see the cons for “Option 2” for problems with custom headers.

#### Cons:

*  On legacy servers the query parameters may cause the request to 404 even if the server has
   ‘/the/font.ttf’. 
*  Likewise for legacy servers the cache may be fragmented by the query string, unless they are
   correctly configured.
*  There’s a limit to how long a URL can be. For requests with a large number of codepoints, we may
   exceed the limit. Would need to fallback to grabbing the whole font in that case.
   
### Option 2 - GET with parameters as headers

```
GET /the/font.ttf
Codepoints-Needed: <base64 encoded set>
Accept-Patch: <list of patch formats>
```

#### Cacheability:

*  Legacy Server: will ignore the headers and caching will work as usual.
*  Patch/Subset Server: server could internally cache the response using the codepoint set in the key.
   Can be served with public caching enabled if a “Vary: Codepoints-Needed, Accept-Patch” header is
   added to the response.

#### Pros:

*  Caching works by default for legacy servers.
*  No concerns about query parameters possibly causing 404’s on legacy servers.
*  No limit on the header value size.

#### Cons:

*  Custom headers will likely trip a requirement for a CORS preflight request. This would
   add an exrta round trip to the first request if the fonts are not hosted on the same domain as
   the content. See [Preflight Requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#Preflighted_requests).
*  Custom headers may be stripped by intermediate proxies. Can mostly be mitigated by requiring HTTPS
   for requests, which we also likely want to do for privacy reasons.
*  Custom headers may need to be registered with the appropriate standards bodies (outside of the
   fonts working group specification).

## Subsequent Requests

*  For range request subsequent requests are sent using http range requests.
*  For patch subset subsequent requests are sent using POST with the parameters specified in the
   request body.
    *  If we’re sending subsequent requests then we know the backend supports patch/subset. So can
       safely use a custom message format in the body of the request.
    *  Disables client caching for patching requests. Caching will likely be ineffective beyond the
       initial request. Servers can still do some caching in the patch/subset implementation.
    *  Reduces the number of additional custom headers needed (if using headers).
    *  Avoids the URL size problem (if using query parameters)
    *  Avoids needed to base64 encode the patch/subset message payload.1




