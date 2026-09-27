"use client";

/**
 * Base component catalog — complete default frontend implementation.
 * Customers override individual slots; unresolved slots fall back here.
 */
import ArchitecturePanel from "./ArchitecturePanel";
import BrandIcon from "./BrandIcon";
import CustomerPanel from "./CustomerPanel";
import FieldRow from "./FieldRow";
import Hero from "./Hero";
import InfoPage from "./InfoPage";
import LeadForm from "./LeadForm";
import LeadList from "./LeadList";
import SiteNav from "./SiteNav";
import Styles from "./Styles";

export const BASE_COMPONENTS = {
  Hero,
  CustomerPanel,
  LeadForm,
  LeadList,
  ArchitecturePanel,
  FieldRow,
  Styles,
  InfoPage,
  SiteNav,
  BrandIcon,
};

export {
  ArchitecturePanel,
  BrandIcon,
  CustomerPanel,
  FieldRow,
  Hero,
  InfoPage,
  LeadForm,
  LeadList,
  SiteNav,
  Styles,
};
