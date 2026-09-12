from __future__ import annotations

from typing import Any

from .models import DeploymentProfile


class KubernetesManifestBuilder:
    """Builds portable Kubernetes objects without requiring a Kubernetes client."""

    def build(self, profile: DeploymentProfile) -> list[dict[str, Any]]:
        labels = {"app": "reproproof", "environment": profile.name.value}
        selector = {"matchLabels": labels}
        return [
            {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": profile.namespace},
            },
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": "reproproof-config",
                    "namespace": profile.namespace,
                },
                "data": {"APP_ENV": profile.name.value},
            },
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": "reproproof-secrets",
                    "namespace": profile.namespace,
                },
                "type": "Opaque",
                "stringData": {
                    name: "REPLACE_AT_DEPLOY_TIME" for name in profile.secrets
                },
            },
            {
                "apiVersion": "v1",
                "kind": "ServiceAccount",
                "metadata": {"name": "reproproof", "namespace": profile.namespace},
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "Role",
                "metadata": {"name": "reproproof", "namespace": profile.namespace},
                "rules": [
                    {
                        "apiGroups": [""],
                        "resources": ["configmaps"],
                        "verbs": ["get", "list"],
                    }
                ],
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "RoleBinding",
                "metadata": {"name": "reproproof", "namespace": profile.namespace},
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": "reproproof",
                        "namespace": profile.namespace,
                    }
                ],
                "roleRef": {
                    "kind": "Role",
                    "name": "reproproof",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
            {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": "reproproof-backend",
                    "namespace": profile.namespace,
                    "labels": labels,
                },
                "spec": {
                    "replicas": profile.replicas,
                    "selector": selector,
                    "strategy": {
                        "type": "RollingUpdate",
                        "rollingUpdate": {"maxUnavailable": 0, "maxSurge": 1},
                    },
                    "template": {
                        "metadata": {"labels": labels},
                        "spec": {
                            "serviceAccountName": "reproproof",
                            "containers": [
                                {
                                    "name": "backend",
                                    "image": profile.backend_image,
                                    "ports": [{"containerPort": 8000}],
                                    "resources": {
                                        "requests": profile.resources,
                                        "limits": profile.resources,
                                    },
                                    "readinessProbe": {
                                        "httpGet": {
                                            "path": "/health/ready",
                                            "port": 8000,
                                        }
                                    },
                                    "livenessProbe": {
                                        "httpGet": {
                                            "path": "/health/live",
                                            "port": 8000,
                                        }
                                    },
                                }
                            ],
                        },
                    },
                },
            },
            {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": "reproproof-backend",
                    "namespace": profile.namespace,
                },
                "spec": {
                    "selector": labels,
                    "ports": [{"port": 8000, "targetPort": 8000}],
                },
            },
            {
                "apiVersion": "autoscaling/v2",
                "kind": "HorizontalPodAutoscaler",
                "metadata": {
                    "name": "reproproof-backend",
                    "namespace": profile.namespace,
                },
                "spec": {
                    "scaleTargetRef": {
                        "apiVersion": "apps/v1",
                        "kind": "Deployment",
                        "name": "reproproof-backend",
                    },
                    "minReplicas": profile.replicas,
                    "maxReplicas": max(profile.replicas * 3, 3),
                    "metrics": [
                        {
                            "type": "Resource",
                            "resource": {
                                "name": "cpu",
                                "target": {
                                    "type": "Utilization",
                                    "averageUtilization": 70,
                                },
                            },
                        }
                    ],
                },
            },
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "NetworkPolicy",
                "metadata": {
                    "name": "reproproof-default-deny",
                    "namespace": profile.namespace,
                },
                "spec": {"podSelector": {}, "policyTypes": ["Ingress", "Egress"]},
            },
            {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "Ingress",
                "metadata": {"name": "reproproof", "namespace": profile.namespace},
                "spec": {
                    "rules": [
                        {
                            "host": profile.host,
                            "http": {
                                "paths": [
                                    {
                                        "path": "/",
                                        "pathType": "Prefix",
                                        "backend": {
                                            "service": {
                                                "name": "reproproof-backend",
                                                "port": {"number": 8000},
                                            }
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                },
            },
            {
                "apiVersion": "v1",
                "kind": "PersistentVolume",
                "metadata": {"name": "reproproof-data"},
                "spec": {
                    "capacity": {"storage": "10Gi"},
                    "accessModes": ["ReadWriteOnce"],
                    "hostPath": {"path": "/var/lib/reproproof"},
                },
            },
            {
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {"name": "reproproof-data", "namespace": profile.namespace},
                "spec": {
                    "accessModes": ["ReadWriteOnce"],
                    "resources": {"requests": {"storage": "10Gi"}},
                },
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {"name": "reproproof-observer"},
                "rules": [
                    {
                        "apiGroups": [""],
                        "resources": ["pods"],
                        "verbs": ["get", "list", "watch"],
                    }
                ],
            },
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRoleBinding",
                "metadata": {"name": "reproproof-observer"},
                "subjects": [
                    {
                        "kind": "ServiceAccount",
                        "name": "reproproof",
                        "namespace": profile.namespace,
                    }
                ],
                "roleRef": {
                    "kind": "ClusterRole",
                    "name": "reproproof-observer",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
        ]
