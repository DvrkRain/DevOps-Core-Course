{{/*
Chart-specific helpers that wrap the shared common-lib templates.
This chart depends on common-lib for name/label generation (see Chart.yaml).
Local overrides can be added here if this chart needs custom behavior.
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common.name" . }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- include "common.chart" . }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info-service.labels" -}}
{{- include "common.labels" . }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info-service.selectorLabels" -}}
{{- include "common.selectorLabels" . }}
{{- end }}

{{/*
Common environment variables for the application container.
Centralizes env var definitions so they can be reused across templates (DRY).
*/}}
{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.appConfig.host | default "0.0.0.0" | quote }}
- name: PORT
  value: {{ .Values.appConfig.port | default "5000" | quote }}
- name: DEBUG
  value: {{ .Values.appConfig.debug | default "False" | quote }}
- name: APP_VERSION
  value: {{ .Chart.AppVersion | quote }}
{{- end -}}
