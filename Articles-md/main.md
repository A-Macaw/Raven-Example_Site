# Hello!
Welcome to ***Raven***, a *barebones* CMS made in [Python!](https://python.org "Python")

## Features
- All of [Markdown](https://daringfireball.net/projects/markdown/ "Markdown")
- Lots of markdown extensions
- [SmartyPants](https://daringfireball.net/projects/smartypants/ "SmartyPants") formatting
- Put an image in the `Images` folder and link it like this: `![Alt text](Images/img.jpg)`

## Planned Features
- Admin Frontend with menus for:  
  - Writing  
  - Publishing  
  - Analytics  
  - Layout and Styling Config

## Examples

### Images
`![Bird](Images/raven.jpg)`  
![Bird](Images/raven.jpg)

### SmartyPants
`--` → --

### Markdown Table
| Nice |        |          |       |
|------|--------|----------|-------|
|      | Simple |          |       |
|      |        | Markdown |       |
|      |        |          | Table |



### Code Hilighting
```python
i = 1
while i <= 100:
  t = ''
  if i % 3 == 0:
    t = t + 'Fizz'
  if i % 5 == 0:
    t = t + 'Buzz'
  if t == '':
    print(i)
  else:
    print(t)
  i += 1
```
