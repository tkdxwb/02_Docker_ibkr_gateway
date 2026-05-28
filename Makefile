COMPOSE ?= docker compose

.DEFAULT_GOAL := help

.PHONY: help up up-1 up-2 up-3 \
	stop stop-1 stop-2 stop-3 down \
	restart-1 restart-2 restart-3 \
	logs logs-1 logs-2 logs-3 ps build \
	health watch

help: ## 显示可用命令
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ---- 启动 ----
up: ## 启动全部三个账户容器
	$(COMPOSE) up -d

up-1: ## 启动账户1  (ib-gateway-1 | API 4001 | VNC 5900)
	$(COMPOSE) up -d ib-gateway-1

up-2: ## 启动账户2  (ib-gateway-2 | API 4011 | VNC 5901)
	$(COMPOSE) up -d ib-gateway-2

up-3: ## 启动账户3  (ib-gateway-3 | API 4021 | VNC 5902)
	$(COMPOSE) up -d ib-gateway-3

# ---- 停止 ----
stop-1: ## 停止账户1 (保留容器)
	$(COMPOSE) stop ib-gateway-1

stop-2: ## 停止账户2 (保留容器)
	$(COMPOSE) stop ib-gateway-2

stop-3: ## 停止账户3 (保留容器)
	$(COMPOSE) stop ib-gateway-3

stop: ## 停止全部 (保留容器)
	$(COMPOSE) stop

down: ## 停止并移除全部容器/网络 (volume 保留)
	$(COMPOSE) down

# ---- 重启 ----
restart-1: ## 重启账户1
	$(COMPOSE) restart ib-gateway-1

restart-2: ## 重启账户2
	$(COMPOSE) restart ib-gateway-2

restart-3: ## 重启账户3
	$(COMPOSE) restart ib-gateway-3

# ---- 日志 / 状态 ----
logs-1: ## 跟踪账户1日志 (看登录/2FA)
	$(COMPOSE) logs -f ib-gateway-1

logs-2: ## 跟踪账户2日志 (看登录/2FA)
	$(COMPOSE) logs -f ib-gateway-2

logs-3: ## 跟踪账户3日志 (看登录/2FA)
	$(COMPOSE) logs -f ib-gateway-3

logs: ## 跟踪全部容器日志
	$(COMPOSE) logs -f

ps: ## 查看容器运行状态
	$(COMPOSE) ps

build: ## 构建/重建镜像
	$(COMPOSE) build

health: ## 巡检三账户健康 (容器状态 + IB API 握手)
	@python3 healthcheck.py

watch: ## 持续巡检 (每 30 秒, 仅状态变化时告警)
	@python3 healthcheck.py --watch 30 --quiet
