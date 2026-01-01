import { DomainResource } from "@smile-cdr/fhirts/dist/FHIR-R4/classes/domainResource";
import axios, { AxiosRequestConfig, isAxiosError } from "axios";
import { FhirUtilities } from "./fhir-utilities";
import { Request } from "express";
import { FhirContext } from "./fhir-context";
import { fhirR4 } from "@smile-cdr/fhirts";

class FhirClient {
  async read<T extends DomainResource>(req: Request, path: string) {
    const fhirContext = this._getFhirContextOrThrow(req);

    return await this._callAxios<T>(
      {
        method: "get",
        url: this._addPath(fhirContext, path),
      },
      req,
    );
  }

  async search(req: Request, resourceType: string, searchParameters: string[]) {
    const fhirContext = this._getFhirContextOrThrow(req);

    return await this._callAxios<fhirR4.Bundle>(
      {
        method: "get",
        url: this._addPath(
          fhirContext,
          `${resourceType}?${searchParameters.join("&")}`,
        ),
      },
      req,
    );
  }

  private async _callAxios<T>(config: AxiosRequestConfig, req: Request) {
    const fhirContext = this._getFhirContextOrThrow(req);
    if (fhirContext.token) {
      config.headers = {
        Authorization: `Bearer ${fhirContext.token}`,
      };
    }

    try {
      const response = await axios(config);
      return response.data as T;
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 404) {
        return null;
      }

      throw error;
    }
  }

  private _getFhirContextOrThrow(req: Request) {
    const fhirContext = FhirUtilities.getFhirContext(req);
    if (!fhirContext) {
      throw new Error("The fhir context could not be retrieved");
    }

    return fhirContext;
  }

  private _addPath(fhirContext: FhirContext, path: string) {
    if (path.startsWith("/")) {
      path = path.substring(1);
    }

    return `${fhirContext.url}/${path}`;
  }
}

export const FhirClientInstance = new FhirClient();
