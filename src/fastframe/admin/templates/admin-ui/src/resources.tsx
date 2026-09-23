import type { ReactElement } from "react";
import {
  AutocompleteInput,
  BooleanField,
  BooleanInput,
  BulkDeleteButton,
  Create,
  Datagrid,
  DateField,
  DateInput,
  DateTimeInput,
  Edit,
  List,
  NumberField,
  NumberInput,
  ReferenceInput,
  required,
  SelectInput,
  SimpleForm,
  TextField,
  TextInput,
} from "react-admin";

import type { FieldSchema, ModelSchema } from "./api";

export interface ResourceViews {
  list: () => ReactElement;
  edit?: () => ReactElement;
  create?: () => ReactElement;
  recordRepresentation: (record: Record<string, unknown>) => string;
}

function sortFromOrdering(ordering: string[]): { field: string; order: "ASC" | "DESC" } | undefined {
  const first = ordering[0];
  if (!first) return undefined;
  if (first.startsWith("-")) return { field: first.slice(1), order: "DESC" };
  return { field: first, order: "ASC" };
}

function referenceResource(reference: string, models: ModelSchema[]): string | undefined {
  const shortName = reference.split(".").pop();
  return models.find((model) => model.name === reference || model.name === shortName)?.resource;
}

function columnFor(fieldName: string, model: ModelSchema): ReactElement | null {
  if (fieldName === "__str__") return null;
  const field = model.fields.find((item) => item.name === fieldName);
  const label = field?.label ?? fieldName;

  if (field?.relationshipName) {
    return (
      <TextField
        key={fieldName}
        source={`${field.relationshipName}.display`}
        label={label}
        sortable={false}
      />
    );
  }
  if (field?.type === "BooleanField") {
    return <BooleanField key={fieldName} source={fieldName} label={label} />;
  }
  if (
    field?.type === "IntegerField" ||
    field?.type === "BigIntegerField" ||
    field?.type === "FloatField" ||
    field?.type === "DecimalField"
  ) {
    return <NumberField key={fieldName} source={fieldName} label={label} />;
  }
  if (field?.type === "DateTimeField" || field?.type === "DateField") {
    return <DateField key={fieldName} source={fieldName} label={label} showTime={field.type === "DateTimeField"} />;
  }
  return <TextField key={fieldName} source={fieldName} label={label} />;
}

export function formFields(
  model: ModelSchema,
  models: ModelSchema[],
  isCreate: boolean,
  options?: { omitPrimaryKey?: boolean },
): ReactElement[] {
  return model.fields
    .map((field) => inputFor(field, models, isCreate, options?.omitPrimaryKey))
    .filter((input): input is ReactElement => input !== null);
}

function inputFor(
  field: FieldSchema,
  models: ModelSchema[],
  isCreate: boolean,
  omitPrimaryKey = false,
): ReactElement | null {
  if (field.writeOnly) {
    if (!isCreate) return null;
    return (
      <TextInput
        key={field.name}
        source={field.name}
        label={field.label}
        type="password"
        helperText={field.helpText || undefined}
        validate={field.required ? [required()] : undefined}
        fullWidth
      />
    );
  }

  if (field.primaryKey) {
    if (isCreate || omitPrimaryKey) return null;
    return <TextInput key={field.name} source={field.name} label={field.label} disabled />;
  }
  if (field.readOnly && isCreate) return null;

  const validate = field.required && !field.readOnly ? [required()] : undefined;
  const helperText = field.helpText || undefined;

  if (field.reference) {
    const reference = referenceResource(field.reference, models);
    if (reference) {
      return (
        <ReferenceInput key={field.name} source={field.name} reference={reference} label={field.label}>
          <AutocompleteInput validate={validate} helperText={helperText} />
        </ReferenceInput>
      );
    }
  }

  if (field.choices?.length) {
    return (
      <SelectInput
        key={field.name}
        source={field.name}
        label={field.label}
        helperText={helperText}
        validate={validate}
        disabled={field.readOnly}
        fullWidth
        choices={field.choices.map((choice) => ({ id: choice.value, name: choice.label }))}
      />
    );
  }

  const common = {
    source: field.name,
    label: field.label,
    helperText,
    validate,
    disabled: field.readOnly,
    fullWidth: true,
  };

  switch (field.type) {
    case "BooleanField":
      return <BooleanInput key={field.name} {...common} />;
    case "IntegerField":
    case "BigIntegerField":
    case "FloatField":
    case "DecimalField":
      return <NumberInput key={field.name} {...common} />;
    case "TextField":
      return <TextInput key={field.name} {...common} multiline rows={4} />;
    case "JSONField":
      return (
        <TextInput
          key={field.name}
          {...common}
          multiline
          rows={6}
          format={(value) => (typeof value === "string" ? value : JSON.stringify(value ?? {}, null, 2))}
          parse={(value) => {
            if (typeof value !== "string" || value.trim() === "") return {};
            try {
              return JSON.parse(value) as unknown;
            } catch {
              return value;
            }
          }}
        />
      );
    case "DateField":
      return <DateInput key={field.name} {...common} />;
    case "DateTimeField":
      return <DateTimeInput key={field.name} {...common} />;
    default:
      return <TextInput key={field.name} {...common} />;
  }
}

export function buildResourceViews(model: ModelSchema, models: ModelSchema[]): ResourceViews {
  const columns = (model.listDisplay.length ? model.listDisplay : ["id"])
    .map((name) => columnFor(name, model))
    .filter((column): column is ReactElement => column !== null);

  const filters = model.searchFields.length
    ? [<TextInput key="q" source="q" label="Search" alwaysOn resettable />]
    : undefined;

  const sort = sortFromOrdering(model.ordering);

  const ListView = () => (
    <List perPage={model.listPerPage || 25} filters={filters} sort={sort}>
      <Datagrid rowClick={model.permissions.edit ? "edit" : "show"} bulkActionButtons={model.permissions.delete ? <BulkDeleteButton /> : false}>
        {columns}
      </Datagrid>
    </List>
  );

  const formInputs = (isCreate: boolean) => formFields(model, models, isCreate);

  const EditView = () => (
    <Edit>
      <SimpleForm>{formInputs(false)}</SimpleForm>
    </Edit>
  );

  const defaultValues = Object.fromEntries(
    model.fields
      .filter((field) => !field.primaryKey && field.default !== undefined)
      .map((field) => [field.name, field.default]),
  );

  const CreateView = () => (
    <Create>
      <SimpleForm defaultValues={defaultValues}>{formInputs(true)}</SimpleForm>
    </Create>
  );

  const labelField = model.listDisplay.find((name) => name !== "__str__" && name !== model.pkField) ?? model.pkField;

  return {
    list: ListView,
    edit: model.permissions.edit ? EditView : undefined,
    create: model.permissions.create ? CreateView : undefined,
    recordRepresentation: (record) => String(record[labelField] ?? record.id ?? ""),
  };
}
