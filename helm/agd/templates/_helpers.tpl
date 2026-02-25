{{/*
Expand the name of the chart.
*/}}
{{- define "agd.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agd.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart label (name + version).
*/}}
{{- define "agd.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels applied to every resource.
*/}}
{{- define "agd.labels" -}}
helm.sh/chart: {{ include "agd.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
agd.io/classification: {{ .Values.classificationLevel | quote }}
{{- end }}

{{/*
Selector labels for a given component (pass component name as .component).
Usage: {{ include "agd.selectorLabels" (dict "component" "auth-svc" "context" .) }}
*/}}
{{- define "agd.selectorLabels" -}}
app.kubernetes.io/name: {{ .component }}
app.kubernetes.io/instance: {{ .context.Release.Name }}
{{- end }}

{{/*
Resolve the image for a service value block.
Prefers global.imageRegistry prefix when set.
Usage: {{ include "agd.image" (dict "img" .Values.authSvc.image "context" .) }}
*/}}
{{- define "agd.image" -}}
{{- $registry := .context.Values.global.imageRegistry -}}
{{- $repo := .img.repository -}}
{{- $tag := .img.tag | default .context.Values.image.tag -}}
{{- if $registry -}}
{{ printf "%s/%s:%s" $registry $repo $tag }}
{{- else -}}
{{ printf "%s:%s" $repo $tag }}
{{- end -}}
{{- end }}

{{/*
Namespace helper.
*/}}
{{- define "agd.namespace" -}}
{{ .Values.namespace | default "agd" }}
{{- end }}

{{/*
Database URL for application services.
*/}}
{{- define "agd.databaseUrl" -}}
postgresql://{{ .Values.postgres.username }}:$(DB_PASSWORD)@postgres:5432/{{ .Values.postgres.database }}
{{- end }}
