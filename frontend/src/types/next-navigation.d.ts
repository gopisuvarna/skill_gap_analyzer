declare module "next/navigation" {
  export interface AppRouterInstance {
    push(href: string): void;
    replace(href: string): void;
    refresh(): void;
  }

  export function useRouter(): AppRouterInstance;
}
