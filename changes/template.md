{% for section, _ in sections.items() %}
{% if section %}
## {{ section }} ({{ versiondata.date }})
{% else %}
## {{ versiondata.version }} ({{ versiondata.date }})
{% endif %}

{% if sections[section] %}
{% for category, val in definitions.items() if category in sections[section] %}
### {{ definitions[category]['name'] }}

{% if definitions[category]['showcontent'] %}
{% for text, values in sections[section][category].items() %}
- {{ text }} ({{ values|join(', ') }})
{% endfor %}

{% else %}
- {{ sections[section][category]['']|join(', ') }}

{% endif %}
{% endfor %}
{% else %}
No significant changes.

{% endif %}
{% endfor %}
