import { http } from "./index";

type AgentConfig = {
    model?: string;
    stream?: boolean;
    enable_think?: boolean;
};

type Send2AgentResponse = {
    content: string;
};

export const agentApi = {
    /**
     * Send a request to the agent.
     * @param {string} agentId Agent identifier.
     * @param {Object} data User input payload.
     * @param {AgentConfig} config Basic runtime config.
     * @param options Native fetch options.
     */
    send2Agent: (
        agentId: string,
        url: string,
        data: Record<string, unknown>,
        config: AgentConfig = {},
        options: RequestInit = {},
    ) => {
        const { signal, headers: extraHeaders, ...restOptions } = options ?? {};
        const headers = new Headers(extraHeaders);
        headers.set("Content-Type", "application/json");

        return http<Send2AgentResponse>(
            url,
            {
                ...restOptions,
                signal,
                method: "POST",
                headers,
                body: JSON.stringify({ ...data, ...config }),
            },
        );
    },
};
