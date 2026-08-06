import ArchitectureViz from "@/components/landing/ArchitectureViz";
import BuiltWith from "@/components/landing/BuiltWith";
import CTA from "@/components/landing/CTA";
import DashboardPreview from "@/components/landing/DashboardPreview";
import FAQ from "@/components/landing/FAQ";
import Features from "@/components/landing/Features";
import Footer from "@/components/landing/Footer";
import GetStarted from "@/components/landing/GetStarted";
import Hero from "@/components/landing/Hero";
import Navbar from "@/components/landing/Navbar";
import SmoothScroll from "@/components/landing/SmoothScroll";
import Stats from "@/components/landing/Stats";

export default function LandingPage() {
  return (
    <>
      <SmoothScroll />
      <Navbar />
      <Hero />
      <BuiltWith />
      <Features />
      <ArchitectureViz />
      <DashboardPreview />
      <Stats />
      <GetStarted />
      <FAQ />
      <CTA />
      <Footer />
    </>
  );
}
