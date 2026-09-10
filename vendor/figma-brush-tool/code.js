(()=>{var U=Object.defineProperty;var W=(t,e,r)=>e in t?U(t,e,{enumerable:!0,configurable:!0,writable:!0,value:r}):t[e]=r;var A=(t,e,r)=>W(t,typeof e!="symbol"?e+"":e,r);const Y=`<!doctype html>
<html>
<head>
  <script>
    try {
      window.localStorage.getItem('x')
    } catch (e) {
      const store = new Map()
      const shim = {
        getItem: (k) => (store.has(k) ? store.get(k) : null),
        setItem: (k, v) => {
          store.set(k, String(v))
        },
        removeItem: (k) => {
          store.delete(k)
        },
        clear: () => {
          store.clear()
        },
        key: (i) => Array.from(store.keys())[i] ?? null,
        get length() {
          return store.size
        },
      }
      Object.defineProperty(window, 'localStorage', { value: shim, configurable: true })
    }
  <\/script>
  <style>
    /* Panel shrink-wraps its content; code.ts resizes the iframe height from
       the 'resize' messages posted below. Width is fixed by code.ts. */
    html, body { margin: 0; padding: 0; height: auto; min-height: 0; }
    #plugin-root { height: auto; }
    body { display: block; }
    body > #plugin-root > fig-footer {
      background-color: var(--figma-color-bg);
      border-radius: 0 0 var(--radius-large) var(--radius-large);
    }
    /* The propskit fill picker opens as a wider dialog; size it explicitly so
       the resize observer can measure its full height. */
    dialog.fig-fill-picker-dialog {
      width: 300px;
      max-width: 300px;
      min-width: 300px;
      max-height: none;
      height: max-content;
    }
  </style>
</head>
<body>
  <div id="plugin-root">
    <fig-content>
      <fig-group name="Brush">
    <fig-field>
      <label>Brush style</label>
      <fig-options id="brush" options="Clean, Sketchy, Marker, Calligraphy, Tapered, Ink brush, Charcoal, Pencil, Felt tip" value="Sketchy"></fig-options>
    </fig-field>
    <fig-field>
      <label>Stroke width</label>
      <fig-slider id="width" type="range" min="1" max="40" step="0.5" units="px" value="5" text></fig-slider>
    </fig-field>
    <fig-field>
      <label>Color</label>
      <fig-input-color id="color" value="#262626FF" alpha="true" picker="figma-native"></fig-input-color>
    </fig-field>
      </fig-group>
      <fig-group name="Advanced">
    <fig-field>
      <label>Variation seed</label>
      <fig-input-number id="seed" value="42" step="1"></fig-input-number>
    </fig-field>
    <fig-field>
      <label>Jitter override</label>
      <fig-slider id="jitterOverride" type="range" min="-1" max="10" step="0.5" value="-1" text></fig-slider>
    </fig-field>
    <fig-field>
      <label>Taper override</label>
      <fig-slider id="taperOverride" type="range" min="-1" max="1" step="0.05" value="-1" text></fig-slider>
    </fig-field>
      </fig-group>
    </fig-content>
    <fig-footer sticky>
      <label id="status-apply"></label>
      <fig-button id="action-apply" type="submit" disabled>Apply brush</fig-button>
    </fig-footer>
  </div>
  <script>
    // Report the shrink-wrapped panel height back to code.ts so it can resize
    // the iframe. A ResizeObserver covers content/control changes; a
    // MutationObserver catches the fill picker dialog opening/closing.
    let lastReportedHeight = 0
    let resizeRaf = 0

    function measurePanelHeight() {
      const root = document.getElementById('plugin-root')
      if (!root) return 0
      let h = Math.ceil(root.getBoundingClientRect().height)
      const openDialog = document.querySelector('dialog.fig-fill-picker-dialog[open]')
      if (openDialog) h = Math.max(h, Math.ceil(openDialog.getBoundingClientRect().bottom))
      return h
    }

    function reportHeight() {
      const h = measurePanelHeight()
      if (h && h !== lastReportedHeight) {
        lastReportedHeight = h
        parent.postMessage({ pluginMessage: { type: 'resize', height: h } }, '*')
      }
    }

    const pluginRoot = document.getElementById('plugin-root')
    if (pluginRoot && typeof ResizeObserver !== 'undefined') {
      new ResizeObserver(() => {
        if (resizeRaf) cancelAnimationFrame(resizeRaf)
        resizeRaf = requestAnimationFrame(reportHeight)
      }).observe(pluginRoot)
    }

    new MutationObserver(() => {
      if (resizeRaf) cancelAnimationFrame(resizeRaf)
      resizeRaf = requestAnimationFrame(reportHeight)
    }).observe(document.body, {
      childList: true,
      attributes: true,
      attributeFilter: ['open'],
      subtree: true,
    })

    function colorValue(id) {
      const value = document.getElementById(id).value
      const hex = String(value || '#000000FF').replace('#', '')
      const read = (start, fallback) => {
        const slice = hex.slice(start, start + 2)
        const parsed = Number.parseInt(slice, 16)
        return Number.isFinite(parsed) ? parsed / 255 : fallback
      }
      return { r: read(0, 0), g: read(2, 0), b: read(4, 0), a: hex.length >= 8 ? read(6, 1) : 1 }
    }

    function colorToHex(value) {
      const color = typeof value === 'object' && value !== null ? value : {}
      const channel = (component, fallback) => {
        const numeric = Number(component)
        return Math.round(Math.max(0, Math.min(1, Number.isFinite(numeric) ? numeric : fallback)) * 255)
          .toString(16)
          .padStart(2, '0')
          .toUpperCase()
      }
      return '#' + channel(color.r, 0) + channel(color.g, 0) + channel(color.b, 0) + channel(color.a, 1)
    }

    function gradientToControlValueJson(value) {
      const g = typeof value === 'object' && value !== null ? value : {}
      const stops = Array.isArray(g.stops) ? g.stops : []
      const pct = (n) => Math.round(Math.max(0, Math.min(1, Number(n))) * 100)
      return JSON.stringify({
        type: 'gradient',
        gradient: {
          type: g.type || 'linear',
          angle: Number.isFinite(Number(g.angle)) ? Number(g.angle) : 0,
          stops: stops.map((s) => ({
            position: pct(s.position),
            color: colorToHex(s.color).slice(0, 7),
            opacity: pct(s.color && s.color.a),
          })),
        },
      })
    }

    function hasParam(values, name) {
      return Object.prototype.hasOwnProperty.call(values, name)
    }

    function setControlValue(id, value) {
      const input = document.getElementById(id)
      if (!input) return
      const next = String(value)
      input.value = next
      input.setAttribute('value', next)
    }

    function setControlChecked(id, value) {
      const input = document.getElementById(id)
      if (!input) return
      input.checked = Boolean(value)
      if (input.checked) {
        input.setAttribute('checked', '')
      } else {
        input.removeAttribute('checked')
      }
    }

    function setPanelParams(values) {
      if (typeof values !== 'object' || values === null) return
      if (hasParam(values, "brush")) setControlValue("brush", values.brush)
      if (hasParam(values, "width")) setControlValue("width", values.width)
      if (hasParam(values, "color")) setControlValue("color", colorToHex(values.color))
      if (hasParam(values, "seed")) setControlValue("seed", values.seed)
      if (hasParam(values, "jitterOverride")) setControlValue("jitterOverride", values.jitterOverride)
      if (hasParam(values, "taperOverride")) setControlValue("taperOverride", values.taperOverride)
    }

    function currentParams() {
      return {
        brush: String(document.getElementById('brush').value),
        width: Number(document.getElementById('width').value),
        color: colorValue('color'),
        seed: Number(document.getElementById('seed').value),
        jitterOverride: Number(document.getElementById('jitterOverride').value),
        taperOverride: Number(document.getElementById('taperOverride').value),
      }
    }
    document.getElementById('action-apply').addEventListener('click', () => {
      parent.postMessage({ pluginMessage: { type: 'action', id: "apply", params: currentParams() } }, '*')
    })

    function postParamsChange(changed) {
      parent.postMessage({ pluginMessage: { type: 'params-change', params: currentParams(), changed: changed } }, '*')
    }

    document.getElementById("brush").addEventListener('change', () => postParamsChange("brush"))
    document.getElementById("width").addEventListener('change', () => postParamsChange("width"))
    document.getElementById("color").addEventListener('input', () => postParamsChange("color"))
    document.getElementById("color").addEventListener('change', () => postParamsChange("color"))
    document.getElementById("seed").addEventListener('change', () => postParamsChange("seed"))
    document.getElementById("jitterOverride").addEventListener('change', () => postParamsChange("jitterOverride"))
    document.getElementById("taperOverride").addEventListener('change', () => postParamsChange("taperOverride"))

    window.onmessage = (event) => {
      const msg = event.data && event.data.pluginMessage
      if (!msg) return
      if (msg.type === 'params-change') {
        setPanelParams(msg.params)
        return
      }
    }


    // code.ts pushes per-action enabled state, button label, and status here on
    // every selection change. addEventListener (not window.onmessage) so this
    // coexists with the spatial/restore message handler.
    window.addEventListener('message', (event) => {
      const msg = event.data && event.data.pluginMessage
      if (!msg || msg.type !== 'action-state' || !msg.actions) return
      {
        const a = msg.actions["apply"]
        const button = document.getElementById('action-apply')
        if (a && button) {
          if (a.enabled === false) button.setAttribute('disabled', '')
          else button.removeAttribute('disabled')
          if (typeof a.label === 'string') button.textContent = a.label
        }
        const status = document.getElementById('status-apply')
        if (a && status && typeof a.status === 'string') status.textContent = a.status
      }
    })

  <\/script>
  <!-- Values are restored by code.ts before figma.showUI paints. -->
</body>
</html>
`,k="4b4bc9f4-6fda-4d68-bd35-49d3940e47ce",C="Brush strokes",T=k+":state",y={brush:"Sketchy",width:5,color:{r:.15,g:.15,b:.15,a:1},seed:42,jitterOverride:-1,taperOverride:-1};let x=y,S=!1;function P(t,e){const r=Number(t);return Number.isFinite(r)?r:e}function v(t,e,r){return Math.max(e,Math.min(r,t))}function K(t,e){if(typeof t!="object"||t===null)return e;const r=t;return{r:v(P(r.r,e.r),0,1),g:v(P(r.g,e.g),0,1),b:v(P(r.b,e.b),0,1),a:v(P(r.a,e.a),0,1)}}function R(t){const e=t!=null?t:{};return{brush:["Clean","Sketchy","Marker","Calligraphy","Tapered","Ink brush","Charcoal","Pencil","Felt tip"].includes(String(e.brush))?String(e.brush):y.brush,width:v(P(e.width,y.width),1,40),color:K(e.color,y.color),seed:v(P(e.seed,y.seed),1,9999),jitterOverride:v(P(e.jitterOverride,y.jitterOverride),-1,10),taperOverride:v(P(e.taperOverride,y.taperOverride),-1,1)}}function z(t){return{type:"SOLID",color:{r:t.r,g:t.g,b:t.b},opacity:t.a}}class L{constructor(){A(this,"commands",[])}coord(e){const r=Number.isFinite(e)?e:0;return Number.isInteger(r)?String(r):Number(r.toFixed(2)).toString()}moveTo(e,r){return this.commands.push("M",this.coord(e),this.coord(r)),this}lineTo(e,r){return this.commands.push("L",this.coord(e),this.coord(r)),this}curveTo(e,r,l,n,s,o){return this.commands.push("C",this.coord(e),this.coord(r),this.coord(l),this.coord(n),this.coord(s),this.coord(o)),this}quadraticCurveTo(e,r,l,n){return this.commands.push("Q",this.coord(e),this.coord(r),this.coord(l),this.coord(n)),this}close(){return this.commands.push("Z"),this}toPathData(){return this.commands.join(" ")}toVectorPath(e="NONZERO"){return{windingRule:e,data:this.toPathData()}}}function N(t){return t.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;")}function Q(t){const e=r=>Math.round(v(r,0,1)*255).toString(16).padStart(2,"0").toUpperCase();return"#"+e(t.r)+e(t.g)+e(t.b)+e(t.a)}function G(t){let e=t;return()=>(e=(e*16807+0)%2147483647,(e-1)/2147483646)}function D(t){const e=t(),r=t();return Math.sqrt(-2*Math.log(Math.max(e,1e-4)))*Math.cos(2*Math.PI*r)}function _(t){var l,n;const e=[],r=t.vectorNetwork;for(const s of r.segments){const o=r.vertices[s.start],p=r.vertices[s.end];(e.length===0||e[e.length-1].x!==o.x||e[e.length-1].y!==o.y)&&e.push({x:o.x,y:o.y});const u=(l=s.tangentStart)!=null?l:{x:0,y:0},d=(n=s.tangentEnd)!=null?n:{x:0,y:0};if(u.x!==0||u.y!==0||d.x!==0||d.y!==0){const h=o.x+u.x,b=o.y+u.y,c=p.x+d.x,m=p.y+d.y;for(let a=.1;a<=.9;a+=.1){const i=1-a,f=i*i*i*o.x+3*i*i*a*h+3*i*a*a*c+a*a*a*p.x,M=i*i*i*o.y+3*i*i*a*b+3*i*a*a*m+a*a*a*p.y;e.push({x:f,y:M})}}e.push({x:p.x,y:p.y})}return e}function X(t,e){if(t.length<2)return t;const r=[t[0]];let l=0;for(let o=1;o<t.length;o++){const p=t[o].x-t[o-1].x,u=t[o].y-t[o-1].y,d=Math.sqrt(p*p+u*u);if(d<.001)continue;const h=p/d,b=u/d;let c=l;for(;c+e<=d;)c+=e,r.push({x:t[o-1].x+h*c,y:t[o-1].y+b*c});l=d-c}const n=t[t.length-1],s=r[r.length-1];return(Math.abs(n.x-s.x)>.1||Math.abs(n.y-s.y)>.1)&&r.push(n),r}function F(t,e,r){if(e<=0)return t;const l=G(r),n=[t[0]];for(let s=1;s<t.length-1;s++)n.push({x:t[s].x+D(l)*e,y:t[s].y+D(l)*e});return n.push(t[t.length-1]),n}function H(t,e,r,l){if(t.length<2)return t;const n=X(t,4),s=n.length,o=[],p=[];for(let u=0;u<s;u++){let d,h;u===0?(d=-(n[1].y-n[0].y),h=n[1].x-n[0].x):u===s-1?(d=-(n[u].y-n[u-1].y),h=n[u].x-n[u-1].x):(d=-(n[u+1].y-n[u-1].y),h=n[u+1].x-n[u-1].x);const b=Math.sqrt(d*d+h*h);b<.001?(d=0,h=1):(d/=b,h/=b);const c=u/Math.max(1,s-1);let m=1;r>0&&(l==="symmetric"?c<r?m=c/r:c>1-r&&(m=(1-c)/r):l==="toward"?c>1-r&&(m=(1-c)/r):l==="away"&&c<r&&(m=c/r)),m=Math.max(.05,m);const a=e/2*m;o.push({x:n[u].x+d*a,y:n[u].y+h*a}),p.push({x:n[u].x-d*a,y:n[u].y-h*a})}return[...o,...p.reverse()]}function $(t,e){switch(t){case"Sketchy":return{width:e,jitter:2.5,passes:2,taper:0,taperDir:"symmetric",cap:"round"};case"Marker":return{width:e*1.8,jitter:0,passes:1,taper:0,taperDir:"symmetric",cap:"round"};case"Calligraphy":return{width:e,jitter:0,passes:1,taper:.3,taperDir:"symmetric",cap:"round"};case"Tapered":return{width:e,jitter:0,passes:1,taper:.4,taperDir:"toward",cap:"round"};case"Ink brush":return{width:e*1.2,jitter:1,passes:1,taper:.25,taperDir:"away",cap:"round"};case"Charcoal":return{width:e*1.5,jitter:3.5,passes:3,taper:.1,taperDir:"symmetric",cap:"round"};case"Pencil":return{width:e*.6,jitter:1.2,passes:2,taper:.05,taperDir:"symmetric",cap:"round"};case"Felt tip":return{width:e*1.3,jitter:.3,passes:1,taper:.15,taperDir:"toward",cap:"round"};default:return{width:e,jitter:0,passes:1,taper:0,taperDir:"symmetric",cap:"square"}}}function ee(t){return[...new Set(t)].filter(e=>!e.removed)}function q(t){const e=ee(t);if(e.length>0)for(const r of e)r.setRelaunchData({[k]:C});else figma.root.setRelaunchData({[k]:C})}function I(){var e;const t=figma.currentPage.selection;return t.length===1&&(e=t[0])!=null?e:null}function O(t){var e;try{const r=JSON.parse(t.getPluginData(T));return(r==null?void 0:r.version)!==1?null:{version:1,params:R(r.params),state:(e=r.state)!=null?e:null}}catch(r){return null}}function Z(t,e,r){t.setPluginData(T,JSON.stringify({version:1,params:e,state:r}))}function te(t){t.setPluginData(T,"")}function re(t,e){return t?e?"Reapply brush":"Apply brush style":"Select a vector path"}function ne(t){return t.length===1&&t[0].type==="VECTOR"}function J(){const t=I();return t==null?null:ne([t])?t:null}async function ae(t,e,r){const l=[e];let n=r;return await(async()=>{if(e.type!=="VECTOR")return;const s=_(e);if(s.length<2)return;const o=$(t.brush,t.width),p=t.jitterOverride>=0?t.jitterOverride:o.jitter,u=t.taperOverride>=0?t.taperOverride:o.taper,d=[];for(let a=0;a<o.passes;a++){const i=F(s,p,t.seed+a*1e3),f=H(i,o.width,u,o.taperDir);d.push(f)}const h=new L;for(const a of d)if(!(a.length<3)){h.moveTo(a[0].x,a[0].y);for(let i=1;i<a.length;i++)h.lineTo(a[i].x,a[i].y);h.close()}const b=h.toPathData(),c=figma.createVector();if(c.name=e.name+" \u2014 "+t.brush,c.vectorPaths=[{windingRule:"NONZERO",data:b}],c.fills=[z(t.color)],c.strokes=[],c.x=e.x,c.y=e.y,e.parent!=null&&"appendChild"in e.parent){const a=e.parent,i=a.children.indexOf(e);a.insertChild(i,c)}e.visible=!1;const m=r==null?void 0:r.outputId;if(m){const a=await figma.getNodeByIdAsync(m);a!=null&&!a.removed&&a.remove()}n={outputId:c.id,centerline:s},l.push(c)})(),{affectedNodes:l,state:n}}async function ie(t,e){var r,l;S=!0;try{const n=await ae(x,t,(l=(r=O(t))==null?void 0:r.state)!=null?l:null);if(Z(t,x,n.state),q(n.affectedNodes),E(),e){const s=n.affectedNodes.filter(o=>o!==t);s.length>0&&figma.viewport.scrollAndZoomIntoView(s),figma.notify(C+" applied")}}catch(n){const s=n instanceof Error?n.message:String(n);throw figma.notify(s,{error:!0}),n}finally{S=!1}}async function oe(t){var l;const e=O(t);if(e==null)return;t.visible=!0;const r=(l=e==null?void 0:e.state)==null?void 0:l.outputId;if(r){const n=await figma.getNodeByIdAsync(r);n!=null&&!n.removed&&n.remove()}te(t),t.setRelaunchData({}),E(),figma.notify(C+" removed")}async function se(t,e,r){const l=[e];let n=r;return await(async()=>{var a;if(e.type!=="VECTOR")return;const s=(a=r==null?void 0:r.centerline)!=null?a:_(e);if(s.length<2)return;const o=$(t.brush,t.width),p=t.jitterOverride>=0?t.jitterOverride:o.jitter,u=t.taperOverride>=0?t.taperOverride:o.taper,d=[];for(let i=0;i<o.passes;i++){const f=F(s,p,t.seed+i*1e3),M=H(f,o.width,u,o.taperDir);d.push(M)}const h=new L;for(const i of d)if(!(i.length<3)){h.moveTo(i[0].x,i[0].y);for(let f=1;f<i.length;f++)h.lineTo(i[f].x,i[f].y);h.close()}const b=h.toPathData(),c=r==null?void 0:r.outputId;let m=null;if(c){const i=await figma.getNodeByIdAsync(c);i!=null&&!i.removed&&i.type==="VECTOR"&&(m=i)}if(m==null&&(m=figma.createVector(),m.x=e.x,m.y=e.y,e.parent!=null&&"appendChild"in e.parent)){const i=e.parent,f=i.children.indexOf(e);i.insertChild(f,m)}m.name=e.name+" \u2014 "+t.brush,m.vectorPaths=[{windingRule:"NONZERO",data:b}],m.fills=[z(t.color)],m.strokes=[],n={outputId:m.id,centerline:s},l.push(m)})(),{affectedNodes:l,state:n}}async function le(t,e){if(x=t,!["brush","width","color","seed","jitterOverride","taperOverride"].includes(e))return;const r=I();if(r==null)return;const l=O(r);if(l!=null){S=!0;try{const n=await se(x,r,l.state);Z(r,x,n.state),q(n.affectedNodes),E()}catch(n){const s=n instanceof Error?n.message:String(n);throw figma.notify(s,{error:!0}),n}finally{S=!1}}}function E(){const t=J(),e=t!=null&&O(t)!=null,r=t!=null;figma.ui.postMessage({type:"action-state",actions:{apply:{enabled:r,label:e?"Remove brush":"Apply brush",status:re(r,e)}}})}function ue(){var r;if(S)return;const t=I(),e=t!=null?O(t):null;x=(r=e==null?void 0:e.params)!=null?r:y,figma.ui.postMessage({type:"params-change",params:x}),E()}const B=I(),j=B!=null?O(B):null;var V;const w=(V=j==null?void 0:j.params)!=null?V:y;x=w;let g=Y;g=g.replace(/(id="brush"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(String(w.brush))+"$2");g=g.replace(/(id="width"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(String(w.width))+"$2");g=g.replace(/(id="color"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(Q(w.color))+"$2");g=g.replace(/(id="seed"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(String(w.seed))+"$2");g=g.replace(/(id="jitterOverride"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(String(w.jitterOverride))+"$2");g=g.replace(/(id="taperOverride"[^>]*\bvalue=")[^"]*(")/g,"$1"+N(String(w.taperOverride))+"$2");figma.root.setRelaunchData({[k]:C});figma.showUI(g,{width:280,height:320});E();figma.on("selectionchange",ue);figma.ui.onmessage=t=>{if(t.type==="resize"){figma.ui.resize(280,Math.max(48,Math.min(900,Math.round(t.height))));return}if(t.type==="action"){if(t.id==="apply"){const e=J();if(e==null)return;O(e)!=null?oe(e):(x=R(t.params),ie(e,!0));return}return}if(t.type==="params-change"){le(R(t.params),t.changed);return}};})();
