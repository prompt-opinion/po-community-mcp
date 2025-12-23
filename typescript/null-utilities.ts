export const NullUtilities = {
  getOrThrow: <T>(
    obj: T | null | undefined,
    errorMessage: string = "Unexpected null reference",
  ) => {
    if (obj) {
      return obj;
    }

    throw new Error(errorMessage);
  },
};
