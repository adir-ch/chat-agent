GO ?= go

ADAPTER_DIR := adapter
SEARCH_DIR := search

ADAPTER_BIN := $(ADAPTER_DIR)/bin/adapter
SEARCH_BIN := $(SEARCH_DIR)/bin/search

.PHONY: all build adapter search clean

all: build

build: adapter search

adapter: $(ADAPTER_BIN)

$(ADAPTER_BIN):
	mkdir -p $(dir $@)
	$(GO) build -o $@ ./$(ADAPTER_DIR)/cmd/adapter

search: $(SEARCH_BIN)

$(SEARCH_BIN):
	mkdir -p $(dir $@)
	$(GO) build -o $@ ./$(SEARCH_DIR)/cmd/search

clean:
	rm -rf $(ADAPTER_DIR)/bin $(SEARCH_DIR)/bin

