s=open('src/bunker17.html').read()
i=s.index('<style>');head=s[:i];rest=s[i:];j=rest.index('</style>')+8
html='''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="theme-color" content="#14110d">
'''+head+'''<style>
:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px);box-sizing:border-box}
html,body{margin:0}
img{max-width:100%}
[hidden]{display:none!important}
</style>
'''+rest[:j]+'''
</head>
<body>
'''+rest[j:]+'''
</body>
</html>
'''
open('www/index.html','w').write(html);print('index.html',len(html))
