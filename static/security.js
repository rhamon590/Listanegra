(function(){
  'use strict';
  function token(){return document.querySelector('meta[name="csrf-token"]')?.content || '';}
  const previousFetch=window.fetch.bind(window);
  window.fetch=function(input,options={}){
    const method=String(options.method || (input instanceof Request ? input.method : 'GET')).toUpperCase();
    if(['POST','PATCH','PUT','DELETE'].includes(method)){
      const url=new URL(typeof input==='string'?input:input.url,location.href);
      if(url.origin===location.origin){
        const headers=new Headers(options.headers || (input instanceof Request?input.headers:{}));
        headers.set('X-CSRF-Token',token());
        options={...options,headers};
      }
    }
    return previousFetch(input,options);
  };
  function protectForm(form){
    if(!form||!['POST','PUT','DELETE','PATCH'].includes((form.method||'GET').toUpperCase()))return;
    let input=form.querySelector('input[name="csrf_token"]');
    if(!input){input=document.createElement('input');input.type='hidden';input.name='csrf_token';form.appendChild(input);}
    input.value=token();
  }
  const actionPattern=/^\/(?:restringir\/\d+|liberar\/\d+|liberar_lista\/\d+|alterar_status_pre_admissao\/\d+\/[\w-]+|aprovar_admissao\/\d+|reprovar_admissao\/\d+|zerar_pre_admissao|limpar-pre-admissoes)$/;
  // Links de ação antigos continuam visíveis, mas são convertidos em POST protegido.
  document.addEventListener('click',e=>{
    const a=e.target.closest('a[href]');if(!a)return;
    const dest=new URL(a.href,location.href);
    if(dest.origin!==location.origin||!actionPattern.test(dest.pathname))return;
    e.preventDefault();e.stopImmediatePropagation();
    const msg=a.dataset.confirmMessage || 'Confirma esta operação?';
    if(!window.confirm(msg))return;
    const form=document.createElement('form');form.method='post';form.action=dest.pathname;form.hidden=true;
    document.body.appendChild(form);protectForm(form);form.submit();
  },true);
  document.addEventListener('submit',event=>protectForm(event.target),true);
  document.addEventListener('DOMContentLoaded',()=>document.querySelectorAll('form').forEach(protectForm));
})();
