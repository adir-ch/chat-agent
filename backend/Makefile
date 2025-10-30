GO ?= go

GIT_VERSION := $(shell git describe --tags --dirty --always 2>/dev/null || echo unknown)

ADAPTER_DIR := adapter
SEARCH_DIR := search

ADAPTER_BIN := $(ADAPTER_DIR)/bin/adapter
SEARCH_BIN := $(SEARCH_DIR)/bin/search

ADAPTER_LDFLAGS := -ldflags "-X chat-agent/backend/adapter/internal/version.BuildVersion=$(GIT_VERSION)"
SEARCH_LDFLAGS := -ldflags "-X chat-agent/backend/search/internal/version.BuildVersion=$(GIT_VERSION)"

.PHONY: all build adapter search clean

all: build

build: adapter search

adapter: $(ADAPTER_BIN)

$(ADAPTER_BIN):
	mkdir -p $(dir $@)
	$(GO) build $(ADAPTER_LDFLAGS) -o $@ ./$(ADAPTER_DIR)/cmd/adapter

search: $(SEARCH_BIN)

$(SEARCH_BIN):
	mkdir -p $(dir $@)
	$(GO) build $(SEARCH_LDFLAGS) -o $@ ./$(SEARCH_DIR)/cmd/search

clean:
	rm -rf $(ADAPTER_DIR)/bin $(SEARCH_DIR)/bin

