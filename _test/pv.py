from wauo.utils import pv

name = "CLOS"
age = 22
male = True
color = "black"
alias = ["thomas", 666, "CLOS"]

pv(name, age, male, alias, color, rstrip=False)
pv(name, age, male, alias, color, newline=False)
